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
        "tasks/review", "tasks/verified", "tasks/failed", "tasks/maintenance",
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

        # Post-execution: failure learning extraction (runs after verifier)
        if agent == "verifier":
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


if __name__ == "__main__":
    main()
