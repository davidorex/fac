"""Factory CLI — the main entry point for all factory commands."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from .config import find_workspace, load_config
from .run_log import RunLogger

console = Console()

# Pipeline downstream mapping: agent_name → list of (relative_dir, suggested_command_or_None).
# A command of None means the entry is informational only — no single agent owns next action.
# This is the single authoritative data structure for pipeline awareness.
PIPELINE_DOWNSTREAM: dict[str, list[tuple[str, Optional[str]]]] = {
    "spec": [
        ("specs/ready", "factory run builder"),
        ("tasks/research", "factory run researcher"),
    ],
    "researcher": [
        ("tasks/research-done", None),
    ],
    "builder": [
        ("tasks/review", "factory run verifier"),
    ],
    "verifier": [
        ("tasks/failed", None),
        ("tasks/verified", None),
    ],
    "librarian": [],
    "operator": [],
}


def print_pipeline_next(agent: str, workspace: Path) -> None:
    """Print pipeline next-step guidance after a successful agent run.

    Checks each downstream directory for the given agent and prints lines
    for directories that contain non-dotfile items.  If no downstream
    directories have work, prints an idle message instead.

    Called only on successful completion (not on exception).  Called even
    when the agent responded NO_REPLY, because work may have been waiting
    from a previous run.
    """
    downstreams = PIPELINE_DOWNSTREAM.get(agent, [])
    active: list[tuple[str, int, Optional[str]]] = []

    for dir_rel, command in downstreams:
        dir_path = workspace / dir_rel
        if dir_path.exists():
            items = [f for f in dir_path.iterdir() if not f.name.startswith(".")]
            if items:
                active.append((dir_rel, len(items), command))

    console.print()
    if not active:
        console.print("  [dim]Pipeline idle — nothing waiting downstream.[/dim]")
    else:
        for dir_rel, count, command in active:
            if command:
                console.print(
                    f"  {dir_rel} has [yellow]{count}[/yellow] item(s)"
                    f" \u2014 next: [bold]{command}[/bold]"
                )
            else:
                console.print(
                    f"  {dir_rel} has [yellow]{count}[/yellow] item(s)"
                )


def run_spec_pipeline_cleanup(workspace: Path, dry_run: bool = False) -> list[str]:
    """Enforce the single-stage invariant for the spec pipeline.

    A spec file may exist in at most one pipeline stage.  When a file
    exists in a downstream stage, any copies in upstream stages are
    removed.  The ordering from earliest to latest is:

        inbox → drafting → ready → archive

    Archive is the terminal state and is never deleted.  The cleanup is
    idempotent — running it multiple times is equivalent to running it
    once.

    Returns a list of log lines describing every deletion (or planned
    deletion when dry_run=True).
    """
    stages = [
        workspace / "specs" / "inbox",
        workspace / "specs" / "drafting",
        workspace / "specs" / "ready",
        workspace / "specs" / "archive",
    ]

    # Build a name → set-of-stage-indices map for existing .md files
    stage_files: list[set[str]] = []
    for stage in stages:
        if stage.exists():
            stage_files.append({f.name for f in stage.iterdir() if f.suffix == ".md"})
        else:
            stage_files.append(set())

    log_lines: list[str] = []

    # For each stage (except the last/archive), check whether a file
    # in a *later* stage supersedes a copy in this stage.
    for upstream_idx, upstream_stage in enumerate(stages[:-1]):
        for downstream_idx in range(upstream_idx + 1, len(stages)):
            downstream_stage = stages[downstream_idx]
            # Files that appear both upstream and downstream → remove upstream copy
            stale = stage_files[upstream_idx] & stage_files[downstream_idx]
            for name in sorted(stale):
                upstream_file = upstream_stage / name
                downstream_label = downstream_stage.relative_to(workspace)
                log_line = (
                    f"Cleaned stale spec: {upstream_file.relative_to(workspace)}"
                    f" (exists in {downstream_label})"
                )
                log_lines.append(log_line)
                if not dry_run and upstream_file.exists():
                    upstream_file.unlink()
                # Remove from the in-memory set so we don't log it again
                # for a higher-priority downstream.
                stage_files[upstream_idx].discard(name)

    # Check for orphaned rebuild briefs in specs/ready/.
    # A rebuild brief is stale when: the brief exists in ready/ AND the
    # corresponding spec has been removed from ready/ (Builder processed it).
    # This is indicated by: {name}.rebuild.md present, {name}.md absent
    # from ready/, and {name}.md present in archive (confirms build cycle ran).
    ready_dir = stages[2]   # specs/ready
    archive_names = stage_files[3]  # filenames present in specs/archive
    ready_names = stage_files[2]    # filenames currently remaining in specs/ready

    if ready_dir.exists():
        for brief_file in sorted(ready_dir.glob("*.rebuild.md")):
            # Derive the spec name: strip .rebuild.md suffix
            spec_filename = brief_file.name[: -len(".rebuild.md")] + ".md"
            spec_in_ready = spec_filename in ready_names
            spec_archived = spec_filename in archive_names
            if not spec_in_ready and spec_archived:
                log_line = (
                    f"Cleaned stale rebuild brief:"
                    f" {brief_file.relative_to(workspace)}"
                    f" (spec no longer in ready/ and is archived)"
                )
                log_lines.append(log_line)
                if not dry_run and brief_file.exists():
                    brief_file.unlink()

    return log_lines


def run_task_review_cleanup(workspace: Path, dry_run: bool = False) -> list[str]:
    """Remove stale files from tasks/review/ that exist in tasks/verified/ or tasks/failed/.

    A task file in tasks/review/ is stale when an exact filename match exists
    in tasks/verified/ or tasks/failed/ (the active, non-versioned slot).
    Versioned failure reports (foo.v1.md) in tasks/failed/ are NOT treated as
    matches — only the base filename foo.md counts.

    Returns a list of log lines describing every deletion (or planned deletion
    when dry_run=True).
    """
    review_dir = workspace / "tasks" / "review"
    verified_dir = workspace / "tasks" / "verified"
    failed_dir = workspace / "tasks" / "failed"

    if not review_dir.exists():
        return []

    # Collect downstream filenames (exact, non-versioned)
    verified_names: set[str] = (
        {f.name for f in verified_dir.iterdir() if f.suffix == ".md"}
        if verified_dir.exists()
        else set()
    )
    # Only base (non-versioned) failure reports — exclude files matching *.v{N}.md
    versioned_pattern = re.compile(r"\.v\d+\.md$")
    failed_names: set[str] = (
        {
            f.name
            for f in failed_dir.iterdir()
            if f.suffix == ".md" and not versioned_pattern.search(f.name)
        }
        if failed_dir.exists()
        else set()
    )

    log_lines: list[str] = []

    for review_file in sorted(review_dir.glob("*.md")):
        name = review_file.name
        if name in verified_names:
            downstream_label = "tasks/verified"
        elif name in failed_names:
            downstream_label = "tasks/failed"
        else:
            continue

        log_line = (
            f"Cleaned stale task: tasks/review/{name}"
            f" (exists in {downstream_label})"
        )
        log_lines.append(log_line)
        if not dry_run and review_file.exists():
            review_file.unlink()

    return log_lines


def resolve_completed_failures(workspace: Path) -> list[str]:
    """Move versioned and active failure reports to tasks/resolved/ after successful verification.

    For each task in tasks/verified/, checks tasks/failed/ for:
    - Active failure report: {task-name}.md
    - Versioned failure reports: {task-name}.v{N}.md

    Appends a ## Resolution section (resolved_by: rebuild) to each found file
    before moving it to tasks/resolved/.

    Returns a list of log lines describing every file moved.
    """
    verified_dir = workspace / "tasks" / "verified"
    failed_dir = workspace / "tasks" / "failed"
    resolved_dir = workspace / "tasks" / "resolved"

    if not verified_dir.exists() or not failed_dir.exists():
        return []

    resolved_dir.mkdir(parents=True, exist_ok=True)

    log_lines: list[str] = []
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    for verified_file in sorted(verified_dir.glob("*.md")):
        task_name = verified_file.stem
        verified_rel = verified_file.relative_to(workspace)

        resolution_section = (
            "\n\n## Resolution\n"
            f"- resolved_by: rebuild\n"
            f"- resolved_at: {now}\n"
            f"- verified_task: {verified_rel}\n"
        )

        # Collect: active report + all versioned reports
        candidates: list[Path] = []
        active = failed_dir / f"{task_name}.md"
        if active.exists():
            candidates.append(active)
        candidates.extend(sorted(failed_dir.glob(f"{task_name}.v*.md")))

        for failed_file in candidates:
            dest = resolved_dir / failed_file.name
            if dest.exists():
                # Already resolved on a prior cycle — skip
                continue
            text = failed_file.read_text()
            failed_file.write_text(text + resolution_section)
            failed_file.rename(dest)
            log_lines.append(
                f"Resolved: tasks/failed/{failed_file.name}"
                f" → tasks/resolved/{failed_file.name}"
            )

    return log_lines


def resolve_task(workspace: Path, task_name: str, reason: str) -> tuple[int, str]:
    """Move an active failure report (and any versioned reports) to tasks/resolved/.

    Appends a ## Resolution section with resolved_by: manual and the provided reason.

    Returns (exit_code, message):
    - 0  — success; message is a multi-line summary of moved files
    - 1  — no active failure report found in tasks/failed/ for task_name
    """
    failed_dir = workspace / "tasks" / "failed"
    resolved_dir = workspace / "tasks" / "resolved"
    active = failed_dir / f"{task_name}.md"

    if not active.exists():
        return 1, f"No failure report found: tasks/failed/{task_name}.md"

    resolved_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    resolution_section = (
        "\n\n## Resolution\n"
        f"- resolved_by: manual\n"
        f"- resolved_at: {now}\n"
        f"- reason: {reason}\n"
    )

    moved: list[str] = []

    # Active report first, then versioned
    candidates: list[Path] = [active]
    candidates.extend(sorted(failed_dir.glob(f"{task_name}.v*.md")))

    for failed_file in candidates:
        dest = resolved_dir / failed_file.name
        text = failed_file.read_text()
        failed_file.write_text(text + resolution_section)
        failed_file.rename(dest)
        moved.append(f"  tasks/failed/{failed_file.name} → tasks/resolved/{failed_file.name}")

    summary = "\n".join(moved)
    return 0, summary


def extract_failure_learnings(workspace: Path) -> list[str]:
    """Extract generalizable learnings from Verifier failure reports.

    Scans every file in tasks/failed/ for a '## Generalizable Learning'
    section.  For each file that contains the section and does not yet
    have a corresponding entry in learnings/failures/, writes a new
    learning file.

    For failure reports that lack the section, logs a non-blocking
    warning.

    Returns a list of log lines (warnings + extraction confirmations).
    """
    failed_dir = workspace / "tasks" / "failed"
    learnings_dir = workspace / "learnings" / "failures"
    log_lines: list[str] = []

    if not failed_dir.exists():
        return log_lines

    learnings_dir.mkdir(parents=True, exist_ok=True)

    # Collect existing learning filenames once for deduplication check
    existing_learning_names = (
        {f.name for f in learnings_dir.iterdir() if f.suffix == ".md"}
        if learnings_dir.exists()
        else set()
    )

    for report_file in sorted(failed_dir.glob("*.md")):
        task_name = report_file.stem
        text = report_file.read_text()

        # Locate the ## Generalizable Learning section
        match = re.search(
            r"^## Generalizable Learning\s*\n(.*?)(?=^## |\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )

        if not match:
            log_lines.append(
                f"Failure report for {task_name} lacks a Generalizable Learning section."
            )
            continue

        learning_content = match.group(1).strip()

        # Deduplication: skip if any existing file contains task_name as a substring
        if any(task_name in name for name in existing_learning_names):
            continue

        # Determine date from today (runtime extraction date)
        today = datetime.now().strftime("%Y-%m-%d")
        learning_filename = f"{today}-{task_name}-verification-failure.md"
        learning_path = learnings_dir / learning_filename

        learning_text = (
            f"# Failure Learning: {task_name}\n\n"
            f"{learning_content}\n\n"
            f"## Source\n"
            f"- Failure report: tasks/failed/{task_name}.md\n"
            f"- Spec: specs/archive/{task_name}.md\n"
            f"- Extracted by: runtime (post-verifier execution)\n"
        )
        learning_path.write_text(learning_text)
        existing_learning_names.add(learning_filename)
        log_lines.append(
            f"Extracted learning: {learning_path.relative_to(workspace)}"
        )

    return log_lines


def _extract_section(text: str, heading: str) -> str | None:
    """Extract the body of a Markdown ## section from *text*.

    Returns the content between *heading* (verbatim, including the ``##``)
    and the next ``##``-level heading or end of file, stripped of leading
    and trailing whitespace.  Returns ``None`` if the heading is not found.
    """
    pattern = rf"^{re.escape(heading)}\s*\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def rebuild_task(workspace: Path, task_name: str) -> tuple[int, str]:
    """Execute the rebuild transition for a failed task.

    Validates prerequisites, copies the archived spec back to ``specs/ready/``,
    versions the failure report, and writes a rebuild brief that captures
    Verifier's remediation guidance from the ``## Path to Resolution``
    section (with fallbacks to ``## Summary`` and full-text if absent).

    Returns ``(exit_code, message)``:

    - ``0`` — success; *message* is a multi-line summary of created/renamed files
    - ``1`` — missing prerequisite; *message* names the missing file(s)
    - ``2`` — spec already in ``specs/ready/``; *message* is a warning string
    """
    archive_spec = workspace / "specs" / "archive" / f"{task_name}.md"
    failed_report = workspace / "tasks" / "failed" / f"{task_name}.md"
    ready_spec = workspace / "specs" / "ready" / f"{task_name}.md"

    # Exit 2: a rebuild or first build is already in progress
    if ready_spec.exists():
        return (
            2,
            f"Spec already in specs/ready/ — rebuild or first build may be in progress.",
        )

    # Exit 1: missing prerequisites
    missing = []
    if not archive_spec.exists():
        missing.append(f"specs/archive/{task_name}.md")
    if not failed_report.exists():
        missing.append(f"tasks/failed/{task_name}.md")
    if missing:
        return 1, f"Missing required files: {', '.join(missing)}"

    # Read failure report before renaming
    failure_text = failed_report.read_text()

    # Version the failure report (find next available N)
    failed_dir = workspace / "tasks" / "failed"
    n = 1
    while (failed_dir / f"{task_name}.v{n}.md").exists():
        n += 1
    versioned_report = failed_dir / f"{task_name}.v{n}.md"
    failed_report.rename(versioned_report)

    # Copy archived spec to ready (archive remains unchanged — terminal)
    shutil.copy2(archive_spec, ready_spec)

    # Extract "What to Fix" — priority order: Path to Resolution → Summary → full text
    what_to_fix = _extract_section(failure_text, "## Path to Resolution")
    if what_to_fix is None:
        what_to_fix = _extract_section(failure_text, "## Summary")
    if what_to_fix is None:
        what_to_fix = failure_text.strip()

    # Extract satisfaction score (looks for N/10 pattern inside Satisfaction Score section)
    score_section = _extract_section(failure_text, "## Satisfaction Score")
    if score_section is not None:
        score_match = re.search(r"\d+/10", score_section)
        prior_score = score_match.group(0) if score_match else score_section[:50].strip()
    else:
        prior_score = "unknown"

    # Write rebuild brief
    versioned_rel = versioned_report.relative_to(workspace)
    rebuild_brief_path = workspace / "specs" / "ready" / f"{task_name}.rebuild.md"
    rebuild_brief_text = (
        f"# Rebuild Brief: {task_name}\n\n"
        f"prior_failure: {versioned_rel}\n"
        f"prior_score: {prior_score}\n\n"
        f"## What to Fix\n"
        f"{what_to_fix}\n"
    )
    rebuild_brief_path.write_text(rebuild_brief_text)

    summary = (
        f"Spec placed:      specs/ready/{task_name}.md\n"
        f"Rebuild brief:    specs/ready/{task_name}.rebuild.md\n"
        f"Versioned failure: {versioned_rel}"
    )
    return 0, summary


# Category display order and labels for `factory needs`
_CATEGORY_DISPLAY_ORDER: list[tuple[str, str]] = [
    ("permission-change", "Permission Changes"),
    ("config-edit", "Config Edits"),
    ("manual-intervention", "Manual Interventions"),
    ("approval", "Approvals"),
]


def _format_age(created_str: str | None) -> str:
    """Format a created timestamp as a human-readable age string."""
    if not created_str:
        return "unknown"
    try:
        created = datetime.fromisoformat(created_str)
        delta = datetime.now() - created
        if delta.total_seconds() < 3600:
            return f"{int(delta.total_seconds() / 60)}m ago"
        elif delta.total_seconds() < 86400:
            return f"{int(delta.total_seconds() / 3600)}h ago"
        else:
            return f"{delta.days}d ago"
    except (ValueError, TypeError):
        return "unknown"


def parse_needs_entries(workspace: Path) -> list[dict]:
    """Parse all needs entries from memory/*/needs.md files.

    Returns a list of dicts with keys:
        id, status, created, category, blocked, context, exact_change,
        agent, file_path.

    Only reads direct subdirectories of memory/ (one level deep), not the
    daily/ or shared/ subdirectories that do not contain needs.md files.
    """
    entries: list[dict] = []
    memory_dir = workspace / "memory"
    if not memory_dir.exists():
        return entries

    for needs_file in sorted(memory_dir.glob("*/needs.md")):
        agent_name = needs_file.parent.name
        text = needs_file.read_text()

        # Split the file on ## headings at line start to isolate entry blocks.
        # Each block starts with "## {id}" and ends at the next "## " or EOF.
        blocks = re.split(r"^(?=## )", text, flags=re.MULTILINE)

        for block in blocks:
            block = block.strip()
            if not block:
                continue
            heading_match = re.match(r"^## (.+)", block)
            if not heading_match:
                continue

            entry_id = heading_match.group(1).strip()

            def get_field(field_name: str, _block: str = block) -> str | None:
                m = re.search(
                    rf"^- {re.escape(field_name)}:\s*(.+)$", _block, re.MULTILINE
                )
                return m.group(1).strip() if m else None

            exact_match = re.search(
                r"^### Exact Change\s*\n(.*?)(?=^##|\Z)",
                block,
                re.MULTILINE | re.DOTALL,
            )

            entries.append(
                {
                    "id": entry_id,
                    "status": get_field("status") or "open",
                    "created": get_field("created"),
                    "category": get_field("category") or "manual-intervention",
                    "blocked": get_field("blocked"),
                    "context": get_field("context"),
                    "exact_change": exact_match.group(1).strip() if exact_match else None,
                    "agent": agent_name,
                    "file_path": needs_file,
                }
            )

    return entries


def resolve_need(workspace: Path, entry_id: str) -> tuple[int, str]:
    """Mark a needs entry as resolved.

    Searches all memory/*/needs.md files for an open entry whose ## heading
    matches entry_id.  Changes ``status: open`` to ``status: resolved`` and
    inserts a ``resolved_at`` timestamp on the line immediately after.

    Returns (exit_code, message):
    - 0 — success; message names the file that was modified
    - 1 — no open entry found with that ID
    """
    memory_dir = workspace / "memory"
    if not memory_dir.exists():
        return 1, f"No open needs entry found with ID: {entry_id}"

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    for needs_file in sorted(memory_dir.glob("*/needs.md")):
        text = needs_file.read_text()

        pattern = re.compile(
            rf"^## {re.escape(entry_id)}\n(.*?)(?=^## |\Z)",
            re.MULTILINE | re.DOTALL,
        )
        match = pattern.search(text)
        if not match:
            continue

        full_entry = match.group(0)
        if "- status: open" not in full_entry:
            # Entry exists but is already resolved — keep looking
            continue

        new_entry = full_entry.replace(
            "- status: open",
            f"- status: resolved\n- resolved_at: {now}",
            1,
        )
        new_text = text.replace(full_entry, new_entry, 1)
        needs_file.write_text(new_text)
        agent = needs_file.parent.name
        return 0, f"Resolved: {entry_id} (memory/{agent}/needs.md)"

    return 1, f"No open needs entry found with ID: {entry_id}"


@click.group()
@click.pass_context
def main(ctx: click.Context) -> None:
    """Factory — local runtime for a team of persistent AI agents."""
    ctx.ensure_object(dict)


@main.command()
@click.option("--workspace", "-w", type=click.Path(), help="Workspace root directory")
def init(workspace: str | None) -> None:
    """Create the workspace directory structure from agents.yaml."""
    ws = Path(workspace) if workspace else Path.cwd()

    dirs = [
        "specs/inbox", "specs/drafting", "specs/ready", "specs/archive",
        "tasks/research", "tasks/research-done", "tasks/building",
        "tasks/review", "tasks/verified", "tasks/failed", "tasks/resolved", "tasks/maintenance",
        "scenarios/meta",
        "skills/shared", "skills/proposed",
        "skills/researcher", "skills/spec", "skills/builder",
        "skills/verifier", "skills/librarian", "skills/operator",
        "memory/shared",
        "memory/daily/researcher", "memory/daily/spec", "memory/daily/builder",
        "memory/daily/verifier", "memory/daily/librarian", "memory/daily/operator",
        "memory/researcher", "memory/spec", "memory/builder",
        "memory/verifier", "memory/librarian", "memory/operator",
        "learnings/failures", "learnings/corrections", "learnings/discoveries",
        "universe/attractor", "universe/context-engineering",
        "universe/synthesis", "universe/willison",
        "projects", "runs",
    ]

    for d in dirs:
        (ws / d).mkdir(parents=True, exist_ok=True)

    console.print(f"[green]Workspace initialized at {ws}[/green]")


@main.command()
@click.argument("agent")
@click.option("--task", type=click.Path(exists=True), help="Task file to assign")
@click.option("--message", "-m", type=str, help="Free text message for the agent")
def run(agent: str, task: str | None, message: str | None) -> None:
    """Invoke an agent. Heartbeat mode if no --task or --message given."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    if agent not in config.agents:
        console.print(
            f"[red]Error:[/red] Unknown agent '{agent}'. "
            f"Available: {', '.join(config.agents.keys())}"
        )
        sys.exit(1)

    agent_config = config.agents[agent]

    # Determine trigger type
    is_heartbeat = not task and not message
    trigger = "heartbeat" if is_heartbeat else ("task" if task else "message")

    # Load task content if specified
    task_content = None
    if task:
        task_content = Path(task).read_text()

    # Set up run logger
    run_logger = RunLogger(
        workspace=config.workspace,
        agent_name=agent,
        trigger=trigger,
        model=agent_config.model,
    )

    console.print(f"[bold]Running {agent}[/bold] ({agent_config.model})")
    console.print(f"  Trigger: {trigger}")
    console.print(f"  Run ID: {run_logger.run_id}")

    # Import and run
    from .llm import run_agent
    from .context import build_context_bar, estimate_tokens, MODEL_CONTEXT_WINDOWS

    try:
        result = run_agent(
            config=config,
            agent_config=agent_config,
            task_content=task_content,
            message=message,
            is_heartbeat=is_heartbeat,
            run_logger=run_logger,
        )

        if result.strip().upper() == "NO_REPLY":
            console.print(f"  [dim]Agent responded: NO_REPLY[/dim]")
        else:
            console.print(f"\n[bold green]Agent response:[/bold green]")
            console.print(result)

        console.print(f"\n[dim]Run logged to runs/{run_logger.run_id}/[/dim]")
        print_pipeline_next(agent, config.workspace)

        # Post-execution: spec pipeline cleanup (runs after every agent)
        cleanup_log = run_spec_pipeline_cleanup(config.workspace)
        for line in cleanup_log:
            console.print(f"  [dim]{line}[/dim]")

        # Post-execution: task review cleanup (runs after every agent)
        task_cleanup_log = run_task_review_cleanup(config.workspace)
        for line in task_cleanup_log:
            console.print(f"  [dim]{line}[/dim]")

        # Post-execution: failure resolution and learning extraction (verifier only)
        if agent == "verifier":
            resolve_log = resolve_completed_failures(config.workspace)
            for line in resolve_log:
                console.print(f"  [dim]{line}[/dim]")

            learning_log = extract_failure_learnings(config.workspace)
            for line in learning_log:
                if line.startswith("Failure report") and "lacks" in line:
                    console.print(f"  [yellow]Warning:[/yellow] {line}")
                else:
                    console.print(f"  [dim]{line}[/dim]")

    except Exception as e:
        console.print(f"[red]Error during agent run:[/red] {e}")
        run_logger.log_outcome(f"ERROR: {e}")
        sys.exit(1)


@main.command()
def status() -> None:
    """Show all agents, last run time, and pipeline status."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    workspace = config.workspace

    # Agent status table
    table = Table(title="Factory Agents")
    table.add_column("Agent", style="bold")
    table.add_column("Model")
    table.add_column("Last Run")
    table.add_column("Heartbeat")
    table.add_column("Shell")

    runs_dir = workspace / "runs"
    for name, agent in config.agents.items():
        # Find most recent run for this agent
        last_run = "never"
        if runs_dir.exists():
            agent_runs = sorted(
                [d for d in runs_dir.iterdir() if d.is_dir() and d.name.endswith(f"-{name}")],
                reverse=True,
            )
            if agent_runs:
                run_name = agent_runs[0].name
                # Parse timestamp from run ID (YYYYMMDD-HHMMSS-agent)
                ts_str = run_name.rsplit(f"-{name}", 1)[0]
                try:
                    ts = datetime.strptime(ts_str, "%Y%m%d-%H%M%S")
                    delta = datetime.now() - ts
                    if delta.total_seconds() < 3600:
                        last_run = f"{int(delta.total_seconds() / 60)}m ago"
                    elif delta.total_seconds() < 86400:
                        last_run = f"{int(delta.total_seconds() / 3600)}h ago"
                    else:
                        last_run = f"{int(delta.days)}d ago"

                    # Check outcome
                    outcome_path = agent_runs[0] / "outcome.md"
                    if outcome_path.exists():
                        content = outcome_path.read_text()
                        if "NO_REPLY" in content:
                            last_run += " (NO_REPLY)"
                except ValueError:
                    last_run = run_name

        table.add_row(name, agent.model, last_run, agent.heartbeat, agent.shell_access)

    console.print(table)

    # Pipeline status
    console.print("\n[bold]Pipeline:[/bold]")
    pipeline_dirs = [
        ("specs/inbox", "specs/inbox"),
        ("specs/drafting", "specs/drafting"),
        ("specs/ready", "specs/ready"),
        ("tasks/building", "tasks/building"),
        ("tasks/review", "tasks/review"),
        ("tasks/verified", "tasks/verified"),
        ("tasks/failed", "tasks/failed"),
        ("tasks/resolved", "tasks/resolved"),
    ]

    for label, dir_path in pipeline_dirs:
        full_path = workspace / dir_path
        if full_path.exists():
            items = [f for f in full_path.iterdir() if not f.name.startswith(".")]
            count = len(items)
            names = ", ".join(f.name for f in items[:3])
            if count > 3:
                names += f", ... (+{count - 3})"
            if count > 0:
                console.print(f"  {label}: [yellow]{count}[/yellow] ({names})")
            else:
                console.print(f"  {label}: [dim]0[/dim]")
        else:
            console.print(f"  {label}: [dim]—[/dim]")


@main.command()
@click.argument("agent", required=False)
@click.option("--last", "-n", type=int, default=5, help="Number of recent runs to show")
def logs(agent: str | None, last: int) -> None:
    """Show recent run logs."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    runs_dir = config.workspace / "runs"
    if not runs_dir.exists():
        console.print("[dim]No runs yet.[/dim]")
        return

    all_runs = sorted(
        [d for d in runs_dir.iterdir() if d.is_dir()],
        reverse=True,
    )

    if agent:
        all_runs = [r for r in all_runs if r.name.endswith(f"-{agent}")]

    for run_dir in all_runs[:last]:
        meta_path = run_dir / "meta.yaml"
        outcome_path = run_dir / "outcome.md"

        meta_str = ""
        if meta_path.exists():
            import yaml
            meta = yaml.safe_load(meta_path.read_text())
            meta_str = f" | {meta.get('trigger', '?')} | {meta.get('model', '?')}"

        outcome = ""
        if outcome_path.exists():
            text = outcome_path.read_text().strip()
            # First 100 chars of outcome
            preview = text.replace("# Outcome\n\n", "")[:100]
            outcome = f" → {preview}"

        # Count tool calls
        tc_dir = run_dir / "tool-calls"
        tc_count = len(list(tc_dir.iterdir())) if tc_dir.exists() else 0

        console.print(
            f"  [bold]{run_dir.name}[/bold]{meta_str} | "
            f"{tc_count} tool calls{outcome}"
        )


@main.command(name="workspace")
def show_workspace() -> None:
    """Show workspace tree with status indicators."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    workspace = config.workspace
    console.print(f"[bold]Workspace:[/bold] {workspace}\n")

    def count_items(path: Path) -> int:
        if not path.exists():
            return 0
        return len([f for f in path.iterdir() if not f.name.startswith(".")])

    sections = [
        ("Specs", [
            ("inbox", "specs/inbox"),
            ("drafting", "specs/drafting"),
            ("ready", "specs/ready"),
            ("archive", "specs/archive"),
        ]),
        ("Tasks", [
            ("research", "tasks/research"),
            ("research-done", "tasks/research-done"),
            ("building", "tasks/building"),
            ("review", "tasks/review"),
            ("verified", "tasks/verified"),
            ("failed", "tasks/failed"),
            ("maintenance", "tasks/maintenance"),
        ]),
        ("Skills", [
            ("shared", "skills/shared"),
            ("proposed", "skills/proposed"),
        ]),
        ("Memory", [
            ("shared", "memory/shared"),
        ]),
        ("Learnings", [
            ("failures", "learnings/failures"),
            ("corrections", "learnings/corrections"),
            ("discoveries", "learnings/discoveries"),
        ]),
    ]

    for section_name, dirs in sections:
        console.print(f"[bold]{section_name}:[/bold]")
        for label, rel_path in dirs:
            n = count_items(workspace / rel_path)
            style = "yellow" if n > 0 else "dim"
            console.print(f"  {label}: [{style}]{n}[/{style}]")
        console.print()


@main.command(name="cleanup-specs")
@click.option("--dry-run", is_flag=True, default=False, help="Show what would be cleaned without deleting.")
def cleanup_specs_cmd(dry_run: bool) -> None:
    """Remove stale spec files that have advanced to a downstream pipeline stage.

    Enforces the single-stage invariant: a spec file exists in at most
    one of inbox / drafting / ready / archive.  When a file appears in a
    downstream stage, copies in upstream stages are removed (archive is
    never touched).
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    log_lines = run_spec_pipeline_cleanup(config.workspace, dry_run=dry_run)

    if not log_lines:
        console.print("[dim]Spec pipeline is clean — no stale files found.[/dim]")
        return

    prefix = "[dry-run] Would clean" if dry_run else "Cleaned"
    for line in log_lines:
        # Replace the leading "Cleaned" with the appropriate prefix for dry-run
        display = line.replace("Cleaned stale spec:", f"{prefix}:")
        console.print(f"  {display}")


@main.command(name="cleanup-tasks")
@click.option("--dry-run", is_flag=True, default=False, help="Show what would be cleaned without deleting.")
def cleanup_tasks_cmd(dry_run: bool) -> None:
    """Remove stale task files from tasks/review/ that have been verified or failed.

    A tasks/review/ file is stale when the same filename exists in
    tasks/verified/ or tasks/failed/ (active, non-versioned slot only).
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    log_lines = run_task_review_cleanup(config.workspace, dry_run=dry_run)

    if not log_lines:
        console.print("[dim]Task review is clean — no stale files found.[/dim]")
        return

    prefix = "[dry-run] Would clean" if dry_run else "Cleaned"
    for line in log_lines:
        display = line.replace("Cleaned stale task:", f"{prefix}:")
        console.print(f"  {display}")


@main.command()
@click.argument("task_name")
@click.option("--reason", required=True, help="How the failure was resolved.")
def resolve(task_name: str, reason: str) -> None:
    """Mark a failed task as resolved and move its report(s) to tasks/resolved/.

    Moves tasks/failed/{task-name}.md (and any versioned .v{N}.md reports)
    to tasks/resolved/, appending a ## Resolution section with the provided
    reason.  Commits the state transition to git.

    \b
    Exit codes:
      0  Task resolved successfully.
      1  No failure report found in tasks/failed/ for {task-name}.
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    exit_code, message = resolve_task(config.workspace, task_name, reason)

    if exit_code == 0:
        console.print(f"[green]Resolved:[/green] {task_name}")
        console.print(message)
        workspace = config.workspace
        subprocess.run(
            ["git", "add", "tasks/failed/", "tasks/resolved/"],
            cwd=workspace,
            capture_output=True,
        )
        result = subprocess.run(
            ["git", "commit", "-m",
             f"Resolve failed task: {task_name}\n\n"
             f"Moved tasks/failed/{task_name}.md (and any versioned reports) to "
             f"tasks/resolved/. Reason: {reason}"],
            cwd=workspace,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            console.print(f"  [dim]State committed to git.[/dim]")
        else:
            console.print(f"  [yellow]Warning:[/yellow] git commit failed: {result.stderr.strip()}")
    elif exit_code == 1:
        console.print(f"[red]Error:[/red] {message}")
        sys.exit(1)


@main.command()
@click.argument("task_name")
def rebuild(task_name: str) -> None:
    """Trigger a rebuild for a failed task.

    Copies the archived spec back to specs/ready/, versions the active
    failure report to tasks/failed/{task-name}.v{N}.md, and writes a
    rebuild brief at specs/ready/{task-name}.rebuild.md containing
    Verifier's remediation guidance.

    Builder will pick up both files on its next run, read the rebuild
    brief, and modify the existing artifacts rather than building from
    scratch.

    \b
    Exit codes:
      0  Rebuild triggered successfully.
      1  Missing specs/archive/{task-name}.md or tasks/failed/{task-name}.md.
      2  Spec already in specs/ready/ — rebuild or first build in progress.
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    exit_code, message = rebuild_task(config.workspace, task_name)

    if exit_code == 0:
        console.print(f"[green]Rebuild triggered:[/green] {task_name}")
        for line in message.splitlines():
            console.print(f"  {line}")
        # Commit the state transition
        workspace = config.workspace
        subprocess.run(
            ["git", "add",
             f"specs/ready/{task_name}.md",
             f"specs/ready/{task_name}.rebuild.md",
             f"tasks/failed/"],
            cwd=workspace,
            capture_output=True,
        )
        result = subprocess.run(
            ["git", "commit", "-m",
             f"Trigger rebuild: {task_name}\n\n"
             f"Copied specs/archive/{task_name}.md → specs/ready/{task_name}.md. "
             f"Versioned failure report. Wrote rebuild brief with Verifier "
             f"remediation guidance for Builder intake."],
            cwd=workspace,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            console.print(f"  [dim]State committed to git.[/dim]")
        else:
            console.print(f"  [yellow]Warning:[/yellow] git commit failed: {result.stderr.strip()}")
    elif exit_code == 1:
        console.print(f"[red]Error:[/red] {message}")
        sys.exit(1)
    elif exit_code == 2:
        console.print(f"[yellow]Warning:[/yellow] {message}")
        sys.exit(2)


@main.command()
@click.option(
    "--resolve",
    "resolve_id",
    default=None,
    metavar="ID",
    help="Mark the entry with this ID as resolved.",
)
@click.option(
    "--all",
    "show_all",
    is_flag=True,
    default=False,
    help="Show resolved entries alongside open ones (default: open only).",
)
def needs(resolve_id: str | None, show_all: bool) -> None:
    """Show or resolve human-action-needed entries across all agents.

    Reads memory/*/needs.md and displays open items grouped by category,
    sorted oldest-first within each category.

    \b
    Exit codes:
      0  Success (including "nothing to show" and successful resolve)
      1  --resolve specified but no open entry found with that ID
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    workspace = config.workspace

    # --resolve path: locate and resolve a single entry, then commit
    if resolve_id is not None:
        exit_code, message = resolve_need(workspace, resolve_id)
        if exit_code == 0:
            console.print(f"[green]{message}[/green]")
            # Stage the modified needs.md and commit
            subprocess.run(
                ["git", "add", "memory/"],
                cwd=workspace,
                capture_output=True,
            )
            result = subprocess.run(
                ["git", "commit", "-m", f"Resolve factory need: {resolve_id}"],
                cwd=workspace,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                console.print(f"  [dim]State committed to git.[/dim]")
            else:
                console.print(
                    f"  [yellow]Warning:[/yellow] git commit failed: {result.stderr.strip()}"
                )
        else:
            console.print(f"[red]Error:[/red] {message}")
            sys.exit(1)
        return

    # Display path
    all_entries = parse_needs_entries(workspace)

    # Warn about duplicate IDs (violates uniqueness invariant)
    seen_ids: dict[str, int] = {}
    for entry in all_entries:
        eid = entry["id"]
        seen_ids[eid] = seen_ids.get(eid, 0) + 1
    for eid, count in seen_ids.items():
        if count > 1:
            console.print(
                f"  [yellow]Warning:[/yellow] Duplicate needs entry ID: {eid}"
            )

    # Filter to open entries (default) or all entries (--all)
    display_entries = all_entries if show_all else [
        e for e in all_entries if e["status"] == "open"
    ]

    open_count = sum(1 for e in all_entries if e["status"] == "open")

    if not display_entries:
        console.print("Factory needs nothing — all clear.")
        return

    # Group by category
    categories: dict[str, list[dict]] = {}
    for entry in display_entries:
        cat = entry["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(entry)

    # Sort entries within each category: oldest created first (None → end)
    for cat_entries in categories.values():
        cat_entries.sort(key=lambda e: e["created"] or "9999")

    label = "open item" if open_count == 1 else "open items"
    console.print(f"\n[bold]Factory Needs[/bold] — [yellow]{open_count}[/yellow] {label}\n")

    # Display in canonical category order, then any unrecognised categories
    known_keys = [k for k, _ in _CATEGORY_DISPLAY_ORDER]
    extra_keys = [k for k in categories if k not in known_keys]
    ordered_keys = known_keys + extra_keys

    for cat_key in ordered_keys:
        if cat_key not in categories:
            continue
        cat_entries = categories[cat_key]
        display_name = next(
            (name for k, name in _CATEGORY_DISPLAY_ORDER if k == cat_key),
            cat_key.replace("-", " ").title(),
        )
        console.print(f"[bold]{display_name}[/bold] ({len(cat_entries)}):")
        for entry in cat_entries:
            age = _format_age(entry["created"])
            eid = entry["id"]
            agent = entry["agent"]
            blocked = entry["blocked"] or "(no description)"
            status_tag = (
                ""
                if entry["status"] == "open"
                else f" [dim]\\[{entry['status']}][/dim]"
            )
            console.print(
                f"  [cyan]{eid:<44}[/cyan]  [dim]\\[{agent}, {age}][/dim]{status_tag}"
            )
            console.print(f"    {blocked}")
        console.print()


if __name__ == "__main__":
    main()
