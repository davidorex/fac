"""Factory CLI — the main entry point for all factory commands."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time as time_mod
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

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
        ("tasks/decisions", "factory decide"),
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

# Canonical invocation order for `factory reflect`.
# Matches the pipeline flow: research → spec → build → verify → curate → operate → review.
PIPELINE_ORDER: list[str] = [
    "researcher", "spec", "builder", "verifier", "librarian", "operator", "reviewer",
]


WHATSAPP_JID = "855718665780@s.whatsapp.net"


def _send_whatsapp(workspace: Path, agent: str, summary: str, next_actions: list[str]) -> None:
    """Send a WhatsApp notification via NanoClaw IPC after an agent run."""
    notifications_dir = workspace / "notifications"
    if not notifications_dir.exists():
        return

    next_lines = "\n".join(f"  → {a}" for a in next_actions[:3]) if next_actions else "  Pipeline idle"
    text = f"*{agent}* completed\n\n{summary}\n\n*Next:*\n{next_lines}"

    # Truncate for WhatsApp readability (phone screen)
    if len(text) > 1500:
        text = text[:1497] + "..."

    msg = {
        "type": "message",
        "chatJid": WHATSAPP_JID,
        "text": text,
    }

    filename = f"{int(time_mod.time() * 1000)}-{agent}-complete.json"
    (notifications_dir / filename).write_text(json.dumps(msg, indent=2) + "\n")


def _resolve_spec_file(workspace: Path, name: str) -> Path | None:
    """Find a spec file by name across pipeline stages.

    Searches inbox/, drafting/, ready/ in that order.
    Accepts with or without .md extension.
    """
    if not name.endswith(".md"):
        name = name + ".md"
    for stage in ("inbox", "drafting", "ready"):
        candidate = workspace / "specs" / stage / name
        if candidate.exists():
            return candidate
    return None


def _count_dir(workspace: Path, rel_path: str) -> tuple[int, list[str]]:
    """Count non-dotfile items in a directory. Returns (count, [names])."""
    d = workspace / rel_path
    if not d.exists():
        return 0, []
    items = sorted(f for f in d.iterdir() if not f.name.startswith("."))
    return len(items), [f.stem for f in items[:5]]


def _model_short(model: str) -> str:
    """Shorten model names for display: claude-opus-4-6 → opus."""
    for prefix in ("claude-", "claude_"):
        model = model.removeprefix(prefix)
    # Strip version suffixes like -4-6, -4-5
    model = re.sub(r"-\d+-\d+$", "", model)
    return model


def _format_age_short(ts_str: str) -> str:
    """Parse a run timestamp and return age string."""
    try:
        ts = datetime.strptime(ts_str, "%Y%m%d-%H%M%S")
    except ValueError:
        return ts_str

    delta = datetime.now() - ts
    if delta.total_seconds() < 3600:
        return f"{int(delta.total_seconds() / 60)}m ago"
    elif delta.total_seconds() < 86400:
        return f"{int(delta.total_seconds() / 3600)}h ago"
    else:
        return f"{int(delta.days)}d ago"


def _agent_last_run(runs_dir: Path, agent_name: str) -> tuple[str, bool]:
    """Get last run age and NO_REPLY status for an agent."""
    if not runs_dir.exists():
        return "never", False

    agent_runs = sorted(
        [d for d in runs_dir.iterdir() if d.is_dir() and d.name.endswith(f"-{agent_name}")],
        reverse=True,
    )
    if not agent_runs:
        return "never", False

    run_name = agent_runs[0].name
    ts_str = run_name.rsplit(f"-{agent_name}", 1)[0]

    age = _format_age_short(ts_str)

    no_reply = False
    outcome_path = agent_runs[0] / "outcome.md"
    if outcome_path.exists():
        content = outcome_path.read_text()
        if "NO_REPLY" in content:
            no_reply = True

    return age, no_reply


def _compute_next_actions(workspace: Path) -> list[str]:
    """Compute actionable next steps based on pipeline state.

    Returns a list of command strings the operator should run, ordered
    by priority.
    """
    actions: list[str] = []

    # Decisions awaiting operator (highest priority)
    dec_count, dec_names = _count_dir(workspace, "tasks/decisions")
    if dec_count > 0:
        for name in dec_names:
            # Check if any entries are awaiting-operator
            dec_file = workspace / "tasks" / "decisions" / f"{name}.md"
            if dec_file.exists():
                text = dec_file.read_text()
                if "awaiting-operator" in text:
                    actions.append(f"factory decide {name}")

    # Needs awaiting operator (observation category excluded — handled via factory triage)
    needs = parse_needs_entries(workspace)
    open_needs = [e for e in needs if e["status"] == "open" and e["category"] != "observation"]
    if open_needs:
        actions.append("factory needs")

    # Factory-internal critical observations need triage
    fi_items = _list_factory_internal(workspace, include_all=False)
    for item in [i for i in fi_items if i["severity"] == "critical"][:2]:
        actions.append(f"factory triage {item['filename']} --promote")

    # Pipeline flow: in priority order
    inbox_count, _ = _count_dir(workspace, "specs/inbox")
    drafting_count, _ = _count_dir(workspace, "specs/drafting")
    ready_count, _ = _count_dir(workspace, "specs/ready")
    research_count, _ = _count_dir(workspace, "tasks/research")
    review_count, _ = _count_dir(workspace, "tasks/review")
    failed_count, _ = _count_dir(workspace, "tasks/failed")

    if research_count > 0:
        actions.append("factory run researcher")
    if inbox_count > 0 or drafting_count > 0:
        _, inbox_names = _count_dir(workspace, "specs/inbox")
        _, drafting_names = _count_dir(workspace, "specs/drafting")
        # Inbox items → factory run spec (initial spec pass)
        if inbox_count > 0:
            if len(inbox_names) == 1:
                actions.append(f"factory run spec {inbox_names[0]}")
            else:
                actions.append(f"factory run spec NAME  ({len(inbox_names)}: {', '.join(inbox_names[:3])})")
        # Drafting items → factory advance (has context to incorporate)
        if drafting_count > 0:
            if len(drafting_names) == 1:
                actions.append(f"factory advance {drafting_names[0]}")
            else:
                actions.append(f"factory advance NAME  ({len(drafting_names)}: {', '.join(drafting_names[:3])})")
    if ready_count > 0:
        _, ready_names = _count_dir(workspace, "specs/ready")
        if len(ready_names) == 1:
            actions.append(f"factory run builder {ready_names[0]}")
        else:
            actions.append(f"factory run builder NAME  ({len(ready_names)}: {', '.join(ready_names[:3])})")
    if review_count > 0:
        actions.append("factory run verifier")
    if failed_count > 0:
        _, failed_names = _count_dir(workspace, "tasks/failed")
        if len(failed_names) == 1:
            actions.append(f"factory rebuild {failed_names[0]}")
        else:
            actions.append(f"factory rebuild NAME  ({len(failed_names)}: {', '.join(failed_names[:3])})")

    # Librarian: suggest after verification completes (new verified work to document)
    verified_count, verified_names = _count_dir(workspace, "tasks/verified")
    if verified_count > 0:
        if len(verified_names) == 1:
            actions.append(f"factory docs {verified_names[0]}")
        else:
            actions.append(f"factory docs NAME  ({len(verified_names)}: {', '.join(verified_names[:3])})")

    return actions


def print_pipeline_next(agent: str, workspace: Path) -> None:
    """Print pipeline next-step guidance after a successful agent run."""
    actions = _compute_next_actions(workspace)

    console.print()
    if not actions:
        console.print("  [dim]Pipeline idle — nothing waiting downstream.[/dim]")
    else:
        console.print("  [bold]Next:[/bold]")
        for action in actions[:3]:
            console.print(f"    → [bold]{action}[/bold]")


def _run_post_execution_passes(
    workspace: Path, agent: str, result: str
) -> list[str]:
    """Run all post-execution kernel passes after an agent completes.

    Returns log lines for display.  Consolidates the duplicated post-execution
    logic from run(), advance(), docs(), and the start loop.
    """
    log: list[str] = []

    for line in run_spec_pipeline_cleanup(workspace):
        log.append(f"[dim]{line}[/dim]")
    for line in run_task_review_cleanup(workspace):
        log.append(f"[dim]{line}[/dim]")
    for line in run_research_cleanup(workspace):
        log.append(f"[dim]{line}[/dim]")

    for line in run_decision_monitor(workspace, agent):
        if "hard gate" in line:
            log.append(f"[yellow]{line}[/yellow]")
        else:
            log.append(f"[dim]{line}[/dim]")

    if agent == "verifier":
        for line in resolve_completed_failures(workspace):
            log.append(f"[dim]{line}[/dim]")
        for line in extract_failure_learnings(workspace):
            if line.startswith("Failure report") and "lacks" in line:
                log.append(f"[yellow]Warning:[/yellow] {line}")
            else:
                log.append(f"[dim]{line}[/dim]")

    for line in extract_surfaced_observations(workspace, agent, result):
        log.append(f"[yellow]{line}[/yellow]")

    for line in promote_needs_observations(workspace, agent):
        log.append(f"[dim]{line}[/dim]")

    for line in cleanup_factory_internal(workspace):
        log.append(f"[dim]{line}[/dim]")

    for line in run_factory_internal_migration(workspace):
        log.append(line)

    return log


def _dispatch_agent(
    config, agent: str, message: str, label: str
) -> tuple[str, bool]:
    """Run an agent with a directed message.  Returns (result, success).

    Handles RunLogger setup, agent invocation, post-execution passes,
    and WhatsApp notification.  Used by the ``start`` loop and can be
    called directly for programmatic dispatch.
    """
    from .llm import run_agent as _run_agent

    agent_config = config.agents[agent]

    run_logger = RunLogger(
        workspace=config.workspace,
        agent_name=agent,
        trigger="message",
        model=agent_config.model,
    )

    console.print(f"\n[bold]Dispatching {agent}[/bold] ({agent_config.model}) — {label}")
    console.print(f"  Run ID: {run_logger.run_id}")

    try:
        result = _run_agent(
            config=config,
            agent_config=agent_config,
            message=message,
            is_heartbeat=False,
            run_logger=run_logger,
        )

        if result.strip().upper() == "NO_REPLY":
            console.print(f"  [dim]Agent responded: NO_REPLY[/dim]")
        else:
            console.print(f"\n[bold green]Agent response:[/bold green]")
            console.print(result)

        console.print(f"\n[dim]Run logged to runs/{run_logger.run_id}/[/dim]")

        for line in _run_post_execution_passes(config.workspace, agent, result):
            console.print(f"  {line}")

        if result.strip().upper() != "NO_REPLY":
            summary = result.strip()
            if len(summary) > 500:
                summary = summary[:497] + "..."
            next_actions = _compute_next_actions(config.workspace)
            _send_whatsapp(config.workspace, agent, summary, next_actions)

        return result, True

    except Exception as e:
        console.print(f"[red]Error during {agent} run:[/red] {e}")
        run_logger.log_outcome(f"ERROR: {e}")
        return str(e), False


def _has_unresolved_decisions(workspace: Path) -> list[str]:
    """Return spec names that have unresolved (awaiting-operator) decision entries."""
    dec_dir = workspace / "tasks" / "decisions"
    if not dec_dir.exists():
        return []
    unresolved = []
    for f in sorted(dec_dir.glob("*.md")):
        text = f.read_text()
        if "awaiting-operator" in text:
            unresolved.append(f.stem)
    return unresolved


def _drafting_specs_ready_to_advance(workspace: Path) -> list[str]:
    """Return names of drafting specs that have research done and decisions resolved.

    A drafting spec is ready to advance when:
    - No pending research requests reference it (tasks/research/{name}* absent
      OR matching tasks/research-done/{name}* present)
    - No unresolved decision entries reference it
    """
    drafting_dir = workspace / "specs" / "drafting"
    if not drafting_dir.exists():
        return []

    research_dir = workspace / "tasks" / "research"
    research_done_dir = workspace / "tasks" / "research-done"
    decisions_dir = workspace / "tasks" / "decisions"

    ready = []
    for spec_file in sorted(drafting_dir.glob("*.md")):
        name = spec_file.stem

        # Check for pending research
        has_pending_research = False
        if research_dir.exists():
            for req in research_dir.glob("*.md"):
                if name in req.stem:
                    # Check if corresponding done exists
                    if not research_done_dir.exists() or not any(
                        d for d in research_done_dir.glob("*.md") if name in d.stem
                    ):
                        has_pending_research = True
                        break

        if has_pending_research:
            continue

        # Check for unresolved decisions
        dec_file = decisions_dir / f"{name}.md"
        if dec_file.exists() and "awaiting-operator" in dec_file.read_text():
            continue

        ready.append(name)

    return ready


# Maximum consecutive rebuild attempts before gating.
_MAX_REBUILD_ATTEMPTS = 3


def _rebuild_attempt_count(workspace: Path, task_name: str) -> int:
    """Count how many versioned failure reports exist for a task."""
    failed_dir = workspace / "tasks" / "failed"
    if not failed_dir.exists():
        return 0
    return len(list(failed_dir.glob(f"{task_name}.v*.md")))


def _compute_next_dispatch(
    workspace: Path, config
) -> tuple[str, str, str, str] | None:
    """Determine the next pipeline action.

    Returns ``(agent, spec_name, dispatch_type, message)`` or ``None``
    when the pipeline is idle or gated.

    Dispatch types: "run", "advance", "docs", "rebuild", "auto-promote".
    The caller handles "auto-promote" directly (no agent invocation).

    Priority order (downstream-first):
      1. tasks/review/       → verifier
      2. tasks/verified/     → docs (librarian)
      3. tasks/failed/       → rebuild + builder
      4. specs/ready/        → builder
      5. drafting + ready    → advance (spec)
      6. tasks/research/     → researcher
      7. factory-internal low → auto-promote
      8. specs/inbox/        → spec
    """
    # --- GATES: check before dispatching ---

    # Gate: unresolved decisions
    unresolved = _has_unresolved_decisions(workspace)
    if unresolved:
        console.print(f"[yellow]Gate:[/yellow] Unresolved decisions: {', '.join(unresolved)}")
        console.print(f"  Resolve with: factory decide {{NAME}}")
        return None

    # Gate: only critical observations block the pipeline.
    # High observations are visible in status and WhatsApp but don't gate.
    fi_items = _list_factory_internal(workspace, include_all=False)
    critical = [i for i in fi_items if i["severity"] == "critical"]
    if critical:
        console.print(f"[yellow]Gate:[/yellow] {len(critical)} critical observations need triage")
        for item in critical[:3]:
            console.print(f"  critical  {item['filename']}")
        console.print(f"  Resolve with: factory triage {{FILE}} --promote or --dismiss")
        return None

    # High observations: warn but don't gate
    high = [i for i in fi_items if i["severity"] == "high"]
    if high:
        console.print(f"[dim]Note: {len(high)} high-severity observations pending triage (not blocking)[/dim]")

    # --- DISPATCH TABLE (downstream-first) ---

    # 1. Review items → verifier
    review_count, review_names = _count_dir(workspace, "tasks/review")
    if review_count > 0:
        name = review_names[0]
        return ("verifier", name, "run",
                f"Verify the task in tasks/review/: {name}")

    # 2. Verified items → docs (librarian)
    verified_count, verified_names = _count_dir(workspace, "tasks/verified")
    if verified_count > 0:
        return ("librarian", verified_names[0], "docs", "")

    # 3. Failed items → rebuild + builder
    failed_count, failed_names = _count_dir(workspace, "tasks/failed")
    if failed_count > 0:
        name = failed_names[0]
        attempts = _rebuild_attempt_count(workspace, name)
        if attempts >= _MAX_REBUILD_ATTEMPTS:
            console.print(f"[yellow]Gate:[/yellow] {name} has failed {attempts} times — needs human direction")
            return None
        return ("builder", name, "rebuild", "")

    # 4. Ready specs → builder
    ready_count, ready_names = _count_dir(workspace, "specs/ready")
    if ready_count > 0:
        name = ready_names[0]
        spec_file = workspace / "specs" / "ready" / f"{name}.md"
        spec_content = spec_file.read_text() if spec_file.exists() else ""
        return ("builder", name, "run",
                f"Implement this spec: {name}\n\n--- {name}.md ---\n{spec_content}")

    # 5. Drafting specs ready to advance
    advanceable = _drafting_specs_ready_to_advance(workspace)
    if advanceable:
        return ("spec", advanceable[0], "advance", "")

    # 6. Research requests → researcher
    research_count, research_names = _count_dir(workspace, "tasks/research")
    if research_count > 0:
        return ("researcher", research_names[0], "run",
                f"Research request waiting: {research_names[0]}")

    # 7. Low-severity factory-internal → auto-promote to inbox
    low_items = [i for i in fi_items if i["severity"] == "low"]
    if low_items:
        return ("", low_items[0]["filename"], "auto-promote", "")

    # 8. Inbox specs → spec
    inbox_count, inbox_names = _count_dir(workspace, "specs/inbox")
    if inbox_count > 0:
        name = inbox_names[0]
        spec_file = workspace / "specs" / "inbox" / f"{name}.md"
        spec_content = spec_file.read_text() if spec_file.exists() else ""
        return ("spec", name, "run",
                f"Work on this specific spec: {name} (currently in inbox/)\n\n"
                f"--- {name}.md ---\n{spec_content}")

    return None


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


def run_research_cleanup(workspace: Path, dry_run: bool = False) -> list[str]:
    """Remove stale files from tasks/research/ that exist in tasks/research-done/.

    A research request in tasks/research/ is stale when an exact filename match
    exists in tasks/research-done/ (the completed deliverable).

    Returns a list of log lines describing every deletion (or planned deletion
    when dry_run=True).
    """
    research_dir = workspace / "tasks" / "research"
    done_dir = workspace / "tasks" / "research-done"

    if not research_dir.exists() or not done_dir.exists():
        return []

    done_names: set[str] = {
        f.name for f in done_dir.iterdir() if f.suffix == ".md"
    }

    log_lines: list[str] = []

    for request_file in sorted(research_dir.glob("*.md")):
        if request_file.name in done_names:
            log_line = (
                f"Cleaned stale research request: tasks/research/{request_file.name}"
                f" (exists in tasks/research-done/)"
            )
            log_lines.append(log_line)
            if not dry_run:
                request_file.unlink()

    return log_lines


def extract_surfaced_observations(
    workspace: Path, agent: str, response: str
) -> list[str]:
    """Kernel safety net: scan agent response for surfaced observations.

    Agents should write observations to needs.md themselves (via the
    human-action-needed skill). This pass catches observations that
    were only mentioned in response prose and persists them directly
    to ``specs/factory-internal/`` as structured observation files.

    Returns log lines describing any extracted observations.
    """
    if not response or response.strip().upper() == "NO_REPLY":
        return []

    # Signal phrases that indicate the agent surfaced something worth persisting.
    # Two categories: general (any agent) and verification-specific (verifier
    # reports often contain structured findings in different language).
    signal_phrases = [
        # General — any agent
        "worth surfacing",
        "worth prioritizing",
        "friction point",
        "friction worth",
        "tooling limitation",
        "operator blindness",
        "known limitation",
        "architectural gap",
        "governance gap",
        "needs prioritizing",
        "worth noting",
        # Verification findings — verifier uses structured report language
        "minor observation",
        "dead variable",
        "dead code",
        "cosmetic",
        "directionally positive",
        "meta-scenario",
        "inherited from",
        "not yet captured",
        "should be addressed",
        "could be improved",
    ]

    # Check if the agent already wrote to needs.md during this run.
    # If so, those entries will be promoted by promote_needs_observations —
    # skip the prose extraction to avoid duplicates.
    needs_file = workspace / "memory" / agent / "needs.md"
    needs_mtime_before = needs_file.stat().st_mtime if needs_file.exists() else 0

    # Find sentences containing signal phrases
    observations: list[str] = []
    for line in response.split("\n"):
        line_lower = line.lower().strip()
        if not line_lower:
            continue
        for phrase in signal_phrases:
            if phrase in line_lower:
                # Clean up markdown formatting
                clean = line.strip().lstrip("0123456789.-*> ")
                if clean and len(clean) > 20:
                    observations.append(clean)
                break

    if not observations:
        return []

    # Check if agent already wrote needs during this run
    needs_mtime_after = needs_file.stat().st_mtime if needs_file.exists() else 0
    if needs_mtime_after > needs_mtime_before:
        # Agent updated needs.md — promote_needs_observations will handle those entries
        return ["[dim]Agent wrote to needs.md during run — skipping kernel extraction[/dim]"]

    # Write extracted observations directly to specs/factory-internal/
    fi_dir = workspace / "specs" / "factory-internal"
    fi_dir.mkdir(parents=True, exist_ok=True)

    log: list[str] = []
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%dT%H:%M:%S")
    ts_str = now.strftime("%Y-%m-%dT%H%M")

    for obs in observations[:3]:  # cap at 3
        severity = "low"  # kernel-extracted observations default to low
        slug = _to_slug(obs[:80])
        filename = f"{ts_str}-{severity}-{slug}.md"

        # Deduplication check
        dup = _find_duplicate_factory_internal(fi_dir, obs)
        if dup:
            log.append(f"[dim]Deduplication: kernel extraction skipped for: {obs[:60]}...[/dim]")
            continue

        content = (
            f"# {slug}\n"
            f"- severity: {severity}\n"
            f"- status: open\n"
            f"- created: {now_str}\n"
            f"- source-agent: {agent}\n"
            f"- source-type: kernel-extraction\n"
            f"\n## Observation\n{obs}\n"
            f"\n## Context\n"
            f"Extracted by kernel from agent response prose "
            f"(agent did not write to needs.md during this run).\n"
        )
        (fi_dir / filename).write_text(content)
        log.append(f"Extracted observation → specs/factory-internal/{filename}")

    return log


def run_decision_monitor(workspace: Path, agent: str) -> list[str]:
    """Scan specs in drafting for structured ambiguities and route them.

    Reads specs/drafting/*.md, finds ### entries under a ## 7 or
    ## Ambiguities heading that have reversibility: and impact: tags.

    Soft gates (reversibility: high + impact: implementation|cosmetic) are
    auto-resolved: the kernel picks the recommended option or the first option
    and writes the decision with status: auto-resolved.

    Hard gates (reversibility: low OR impact: governance) are written with
    status: awaiting-operator.

    Results are written to tasks/decisions/{spec-name}.md.  Returns log lines.
    Only runs after spec or builder agents.
    """
    if agent not in ("spec", "builder"):
        return []

    drafting_dir = workspace / "specs" / "drafting"
    decisions_dir = workspace / "tasks" / "decisions"

    if not drafting_dir.exists():
        return []

    log_lines: list[str] = []
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    for spec_file in sorted(drafting_dir.glob("*.md")):
        text = spec_file.read_text()

        # Find ambiguity sections: ## 7 or ## Ambiguities
        ambiguity_match = re.search(
            r"^## (?:7\.?\s*Ambiguities|Ambiguities Requiring Human Decision)\b.*?\n"
            r"(.*)",
            text,
            re.MULTILINE | re.DOTALL,
        )
        if not ambiguity_match:
            continue

        ambiguity_text = ambiguity_match.group(1)

        # Parse individual entries (### headings within the ambiguity section)
        entry_blocks = re.split(r"(?=^### )", ambiguity_text, flags=re.MULTILINE)

        entries: list[dict] = []
        for block in entry_blocks:
            block = block.strip()
            heading_match = re.match(r"^### (.+)", block)
            if not heading_match:
                continue

            entry_id = heading_match.group(1).strip()

            def _get(field: str, _block: str = block) -> str | None:
                m = re.search(
                    rf"^- {re.escape(field)}:\s*(.+)$", _block, re.MULTILINE
                )
                return m.group(1).strip().lower() if m else None

            reversibility = _get("reversibility") or "unknown"
            impact = _get("impact") or "unknown"
            status = _get("status")

            # Skip entries already resolved or not open
            if status and status not in ("open",):
                continue

            # Extract recommendation if present
            rec_match = re.search(
                r"\*\*Recommendation[:\*]*\*?\*?\s*(.*?)(?=^###|\Z)",
                block, re.MULTILINE | re.DOTALL,
            )
            recommendation = rec_match.group(1).strip() if rec_match else None

            # Extract first option as fallback for auto-resolve
            first_option_match = re.search(
                r"^\*\*\(a\)\*\*\s*(.+)$", block, re.MULTILINE,
            )
            first_option = first_option_match.group(1).strip() if first_option_match else None

            # Classify: soft or hard gate
            is_soft = (
                reversibility == "high"
                and impact in ("implementation", "cosmetic")
            )

            entries.append({
                "id": entry_id,
                "reversibility": reversibility,
                "impact": impact,
                "is_soft": is_soft,
                "recommendation": recommendation,
                "first_option": first_option,
                "block": block,
            })

        if not entries:
            continue

        # Write decisions file
        spec_name = spec_file.stem
        decision_file = decisions_dir / f"{spec_name}.md"
        decisions_dir.mkdir(parents=True, exist_ok=True)

        lines: list[str] = [f"# Decisions: {spec_name}\n"]
        n_auto = 0
        n_hard = 0

        for e in entries:
            lines.append(f"### {e['id']}")

            if e["is_soft"]:
                # Auto-resolve: pick recommendation or first option
                chosen = e["recommendation"] or e["first_option"] or "first option"
                lines.append(f"- status: auto-resolved")
                lines.append(f"- decided-by: kernel")
                lines.append(f"- decided-at: {now}")
                lines.append(f"- answer: {chosen}")
                lines.append(f"- reversibility: {e['reversibility']}")
                lines.append(f"- impact: {e['impact']}")
                n_auto += 1
            else:
                # Hard gate: awaiting operator
                lines.append(f"- status: awaiting-operator")
                lines.append(f"- reversibility: {e['reversibility']}")
                lines.append(f"- impact: {e['impact']}")
                n_hard += 1

            # Preserve the original options/recommendation text
            lines.append("")
            lines.append(e["block"])
            lines.append("")

        decision_file.write_text("\n".join(lines))

        if n_auto > 0:
            log_lines.append(
                f"Decision Monitor: {n_auto} ambiguity(s) auto-resolved for {spec_name}"
            )
        if n_hard > 0:
            log_lines.append(
                f"Decision Monitor: {n_hard} hard gate(s) for {spec_name}"
                f" — run: factory decide {spec_name}"
            )

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

# Severity heuristics for factory-internal observation classification.
# Terms are checked in order: first match wins.
_CRITICAL_TERMS: list[str] = [
    "pipeline blocked", "data loss", "governance gap", "security",
    "breaks", "cannot proceed", "integrity",
]
_HIGH_TERMS: list[str] = [
    "friction", "gap", "missing", "stale", "incorrect",
    "degrades", "not firing", "accumulate",
]

_FACTORY_INTERNAL_SEVERITY_ORDER: dict[str, int] = {
    "critical": 0, "high": 1, "low": 2,
}


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


def _snapshot_needs_ids(workspace: Path) -> set[str]:
    """Return the set of all entry IDs currently present in memory/*/needs.md files.

    Used by ``factory reflect`` to measure how many new entries agents write
    during a reflection pass (post-snapshot minus pre-snapshot).
    """
    entries = parse_needs_entries(workspace)
    return {e["id"] for e in entries}


def _to_slug(text: str, max_len: int = 50) -> str:
    """Convert arbitrary text to a kebab-case slug (max_len chars)."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    slug = text[:max_len].rstrip("-")
    return slug or "observation"


def _assign_severity(blocked: str) -> str:
    """Classify observation severity from *blocked* text via keyword heuristics."""
    lower = blocked.lower()
    for term in _CRITICAL_TERMS:
        if term in lower:
            return "critical"
    for term in _HIGH_TERMS:
        if term in lower:
            return "high"
    return "low"


def _extract_needs_observation(block: str) -> str:
    """Extract the observation text from a needs.md entry block.

    Prefers the ``- blocked:`` field.  Falls back to non-field body paragraphs
    for entries that do not use the canonical format (e.g. reviewer entries
    with inline body text instead of a ``blocked:`` field).
    """
    blocked_m = re.search(r"^- blocked:\s*(.+)$", block, re.MULTILINE)
    if blocked_m:
        return blocked_m.group(1).strip()

    # Fallback: collect non-field, non-heading content lines
    lines = []
    for line in block.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("## ") or stripped.startswith("### "):
            continue
        if re.match(r"^- [\w-]+:", stripped):
            continue
        lines.append(stripped)
    body = " ".join(lines).strip()
    return body[:300] if body else "(no description)"


def _find_duplicate_factory_internal(fi_dir: Path, obs_text: str) -> Path | None:
    """Return an existing open factory-internal file whose ## Observation matches *obs_text*.

    Uses normalised whitespace comparison of the first 200 characters.
    Returns None when no duplicate exists or when fi_dir is absent.
    """
    if not fi_dir.exists():
        return None
    norm = re.sub(r"\s+", " ", obs_text[:200]).strip().lower()
    for f in sorted(fi_dir.glob("*.md")):
        if f.name.startswith("."):
            continue
        content = f.read_text()
        status_m = re.search(r"^- status:\s*(\S+)", content, re.MULTILINE)
        if status_m and status_m.group(1).strip() != "open":
            continue
        obs_m = re.search(
            r"^## Observation\s*\n(.*?)(?=^## |\Z)", content, re.MULTILINE | re.DOTALL
        )
        if obs_m:
            existing_norm = re.sub(r"\s+", " ", obs_m.group(1)[:200]).strip().lower()
            if existing_norm == norm:
                return f
    return None


def _parse_factory_internal_file(filepath: Path) -> dict:
    """Parse a factory-internal observation file into a dict."""
    content = filepath.read_text()

    def _get(field: str) -> str | None:
        m = re.search(rf"^- {re.escape(field)}:\s*(.+)$", content, re.MULTILINE)
        return m.group(1).strip() if m else None

    obs_m = re.search(
        r"^## Observation\s*\n(.*?)(?=^## |\Z)", content, re.MULTILINE | re.DOTALL
    )
    obs_text = obs_m.group(1).strip() if obs_m else ""

    title_m = re.match(r"^# (.+)", content)
    title = title_m.group(1).strip() if title_m else filepath.stem

    # Extract slug: strip date-severity prefix from filename
    slug_m = re.match(
        r"^\d{4}-\d{2}-\d{2}T\d{4}-(critical|high|low)-(.+)$",
        filepath.stem,
    )
    slug = slug_m.group(2) if slug_m else filepath.stem

    return {
        "filename": filepath.name,
        "filepath": filepath,
        "slug": slug,
        "title": title,
        "severity": _get("severity") or "low",
        "status": _get("status") or "open",
        "created": _get("created"),
        "source_agent": _get("source-agent") or "unknown",
        "source_type": _get("source-type") or "unknown",
        "promoted_to": _get("promoted_to"),
        "promoted_at": _get("promoted_at"),
        "dismissed_reason": _get("dismissed_reason"),
        "dismissed_at": _get("dismissed_at"),
        "observation": obs_text,
    }


def _list_factory_internal(
    workspace: Path, include_all: bool = False
) -> list[dict]:
    """Return factory-internal observation files sorted by severity then age.

    When *include_all* is False (default), only ``open`` files are returned.
    """
    fi_dir = workspace / "specs" / "factory-internal"
    if not fi_dir.exists():
        return []
    items = []
    for f in fi_dir.glob("*.md"):
        if f.name.startswith("."):
            continue
        item = _parse_factory_internal_file(f)
        if not include_all and item["status"] != "open":
            continue
        items.append(item)
    items.sort(key=lambda x: (
        _FACTORY_INTERNAL_SEVERITY_ORDER.get(x["severity"], 99),
        x["created"] or "",
    ))
    return items


def _resolve_factory_internal(
    fi_dir: Path, filename_or_slug: str
) -> tuple[list[Path], str]:
    """Resolve a filename or slug to matching factory-internal files.

    Returns ``(matches, error_message)``.  On success *error_message* is empty.
    On failure *matches* is empty.
    """
    if not fi_dir.exists():
        return [], "specs/factory-internal/ does not exist"

    # Try exact filename match
    candidate = fi_dir / filename_or_slug
    if not filename_or_slug.endswith(".md"):
        candidate = fi_dir / (filename_or_slug + ".md")
    if candidate.exists():
        return [candidate], ""

    # Slug substring match against all files
    matches = [
        f for f in sorted(fi_dir.glob("*.md"))
        if not f.name.startswith(".") and filename_or_slug in f.name
    ]
    if not matches:
        return [], f"No factory-internal file found matching: {filename_or_slug}"
    return matches, ""


def promote_needs_observations(workspace: Path, agent: str) -> list[str]:
    """Promote ``category: observation`` entries from ``memory/{agent}/needs.md``.

    For each open observation entry, creates a structured file in
    ``specs/factory-internal/`` and updates the needs.md entry to
    ``status: promoted`` with a ``promoted_to`` field.

    Returns a list of log lines.
    """
    needs_file = workspace / "memory" / agent / "needs.md"
    if not needs_file.exists():
        return []

    fi_dir = workspace / "specs" / "factory-internal"
    fi_dir.mkdir(parents=True, exist_ok=True)

    text = needs_file.read_text()
    blocks = re.split(r"^(?=## )", text, flags=re.MULTILINE)

    log: list[str] = []
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%dT%H:%M:%S")
    ts_str = now.strftime("%Y-%m-%dT%H%M")
    updates: list[tuple[str, str]] = []  # (old_block, new_block)

    for block in blocks:
        block_stripped = block.strip()
        if not block_stripped:
            continue
        heading_m = re.match(r"^## (.+)", block_stripped)
        if not heading_m:
            continue

        status_m = re.search(r"^- status:\s*(\S+)", block_stripped, re.MULTILINE)
        cat_m = re.search(r"^- category:\s*(\S+)", block_stripped, re.MULTILINE)

        if not status_m or status_m.group(1).strip() != "open":
            continue
        if not cat_m or cat_m.group(1).strip() != "observation":
            continue

        entry_id = heading_m.group(1).strip()

        # Get created/filed timestamp
        created_m = re.search(
            r"^- (?:created|filed):\s*(.+)$", block_stripped, re.MULTILINE
        )
        created = created_m.group(1).strip() if created_m else now_str

        # Extract observation text
        obs_text = _extract_needs_observation(block_stripped)

        # Assign severity
        severity = _assign_severity(obs_text)

        # Generate filename
        slug = _to_slug(obs_text[:80])
        filename = f"{ts_str}-{severity}-{slug}.md"
        fi_path = fi_dir / filename

        # Deduplication: if matching open file exists, point promoted_to there
        dup = _find_duplicate_factory_internal(fi_dir, obs_text)
        if dup:
            promoted_to = f"specs/factory-internal/{dup.name}"
            log.append(
                f"[dim]Deduplication: {entry_id} matches {dup.name} — skipped creation[/dim]"
            )
        else:
            # Create factory-internal file
            ctx_file = workspace / "memory" / agent / "needs.md"
            content = (
                f"# {slug}\n"
                f"- severity: {severity}\n"
                f"- status: open\n"
                f"- created: {created}\n"
                f"- source-agent: {agent}\n"
                f"- source-type: needs-promotion\n"
                f"\n## Observation\n{obs_text}\n"
                f"\n## Context\n"
                f"Promoted from needs.md entry: {entry_id}. "
                f"Agent: {agent}. Source file: {ctx_file.relative_to(workspace)}.\n"
            )
            fi_path.write_text(content)
            promoted_to = f"specs/factory-internal/{filename}"
            log.append(
                f"Promoted observation: {entry_id} → {promoted_to}"
            )

        # Schedule needs.md update: mark as promoted
        old_block = block  # preserve original (may include leading whitespace from split)
        new_block = re.sub(
            r"(^- status:\s*)open",
            rf"\g<1>promoted\n- promoted_to: {promoted_to}",
            old_block,
            count=1,
            flags=re.MULTILINE,
        )
        updates.append((old_block, new_block))

    # Apply needs.md updates
    if updates:
        new_text = text
        for old, new in updates:
            new_text = new_text.replace(old, new, 1)
        needs_file.write_text(new_text)

    return log


def run_factory_internal_migration(workspace: Path) -> list[str]:
    """One-time migration: promote all open observation entries from all agents.

    Creates a ``.migrated`` sentinel in ``specs/factory-internal/`` after
    running so the migration does not repeat on subsequent invocations.
    Idempotent — entries already marked ``status: promoted`` are skipped
    because ``promote_needs_observations`` only acts on ``status: open`` entries.

    Returns log lines.
    """
    fi_dir = workspace / "specs" / "factory-internal"
    migrated_marker = fi_dir / ".migrated"

    if migrated_marker.exists():
        return []

    fi_dir.mkdir(parents=True, exist_ok=True)
    log: list[str] = ["[dim]Running one-time factory-internal migration…[/dim]"]

    memory_dir = workspace / "memory"
    if memory_dir.exists():
        for needs_file in sorted(memory_dir.glob("*/needs.md")):
            agent_name = needs_file.parent.name
            agent_log = promote_needs_observations(workspace, agent_name)
            log.extend(agent_log)

    migrated_marker.write_bytes(b"")
    log.append("[dim]Migration complete — marker written.[/dim]")
    return log


def cleanup_factory_internal(
    workspace: Path, dry_run: bool = False
) -> list[str]:
    """GC pass: remove factory-internal files when lifecycle criteria are met.

    Removes:
    - ``promoted`` files whose ``promoted_to`` spec exists in ``specs/archive/``
    - ``dismissed`` files whose ``dismissed_at`` is more than 30 days ago

    Returns log lines.
    """
    fi_dir = workspace / "specs" / "factory-internal"
    if not fi_dir.exists():
        return []

    archive_dir = workspace / "specs" / "archive"
    archive_names: set[str] = (
        {f.name for f in archive_dir.glob("*.md")}
        if archive_dir.exists()
        else set()
    )

    log: list[str] = []
    now = datetime.now()

    for f in sorted(fi_dir.glob("*.md")):
        if f.name.startswith("."):
            continue
        content = f.read_text()
        status_m = re.search(r"^- status:\s*(\S+)", content, re.MULTILINE)
        status = status_m.group(1).strip() if status_m else "open"

        if status == "promoted":
            pt_m = re.search(r"^- promoted_to:\s*(.+)$", content, re.MULTILINE)
            if pt_m:
                promoted_to_path = Path(pt_m.group(1).strip())
                inbox_name = promoted_to_path.name
                if inbox_name in archive_names:
                    log.append(
                        f"Cleaned factory-internal: {f.name}"
                        f" (promoted spec archived)"
                    )
                    if not dry_run:
                        f.unlink()

        elif status == "dismissed":
            da_m = re.search(r"^- dismissed_at:\s*(.+)$", content, re.MULTILINE)
            if da_m:
                try:
                    dismissed_at = datetime.fromisoformat(da_m.group(1).strip())
                    if (now - dismissed_at).days >= 30:
                        log.append(
                            f"Cleaned factory-internal: {f.name}"
                            f" (dismissed 30+ days ago)"
                        )
                        if not dry_run:
                            f.unlink()
                except (ValueError, TypeError):
                    pass

    return log


def _agent_yaml_block(workspace: Path, agent_name: str) -> str:
    """Return the agents.yaml YAML block for *agent_name* as a plain-text string.

    Re-reads agents.yaml and serializes just the named agent's section back
    to YAML, so agents can see their own configuration without the runtime
    needing to grant them read access to agents.yaml directly.
    """
    config_path = workspace / "agents.yaml"
    with open(config_path) as f:
        raw: dict = yaml.safe_load(f)
    agent_data = raw.get("agents", {}).get(agent_name, {})
    return yaml.dump({agent_name: agent_data}, default_flow_style=False, sort_keys=False)


_META_SCENARIO_CONTENT = """\
# Factory Meta-Scenario

A solo developer with a new project idea should be able to describe it in 2-3 sentences, leave, and come back to find: a complete NLSpec they can review, a working implementation, a verification assessment, and a list of what the system learned from building it. The developer's only job is to approve the spec and approve the final result. Everything in between is the factory's problem.

## Evaluation Guidance

This is a directional criterion, not a pass/fail gate. The factory is not yet at meta-scenario fulfillment. When evaluating factory infrastructure changes, ask: does this change move the factory closer to or further from this scenario?

- Closer: changes that increase pipeline autonomy, improve reliability, strengthen self-correction, reduce required human intervention for routine operations
- Further: changes that add manual steps, create ambiguity in the pipeline, lose information between stages, or require human expertise to interpret agent output

Each factory infrastructure task should be evaluated for directional alignment. Document the reasoning.

## Source

Blueprint line 586-589: "Write this into `scenarios/meta/factory-itself.md` on day one."
"""

_SCENARIO_TEMPLATE_CONTENT = """\
# Scenario: [Title]

<!-- Copy this file for each scenario. Name copies scenario-001.md, scenario-002.md, etc. -->
<!-- Delete this _template.md file or leave it — it is excluded from scenario counts. -->

## User Story

[Describe a specific end-to-end user interaction. Who is the user? What do they want to accomplish? What do they do step by step? What do they see at each step?]

## Expected Behavior

[Describe the observable outcomes. What should happen at each step? Include both the happy path and edge cases this scenario tests.]

## Why This Matters

[What aspect of the spec does this scenario stress-test? What could go wrong if this scenario fails? What would a user feel if this scenario broke?]
"""

_SCENARIO_PROJECT_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def check_scenario_warning(workspace: Path) -> str | None:
    """Return a warning string when the meta-scenario file is absent, else None.

    Used by the ``run`` command to warn before invoking Verifier when no
    scenario holdouts have been initialised.
    """
    meta = workspace / "scenarios" / "meta" / "factory-itself.md"
    if not meta.exists():
        return (
            "No scenario holdouts found. Verification will be spec-matching only. "
            "Run `factory scenario init-meta` to create the meta-scenario."
        )
    return None


def _scenario_coverage(workspace: Path) -> dict:
    """Compute scenario coverage stats for ``factory status``.

    Returns a dict with:
        directories (int)   — number of subdirs under scenarios/
        total_files (int)   — total scenario .md files (excl. _template.md, satisfaction.md)
        meta_exists (bool)  — whether scenarios/meta/factory-itself.md exists
        warn (bool)         — True if tasks need verification but meta is absent
    """
    scenarios_dir = workspace / "scenarios"
    meta_path = workspace / "scenarios" / "meta" / "factory-itself.md"

    directories = 0
    total_files = 0
    meta_exists = meta_path.exists()

    if scenarios_dir.exists():
        for sub in scenarios_dir.iterdir():
            if sub.is_dir():
                directories += 1
                for f in sub.glob("*.md"):
                    if f.name not in ("_template.md", "satisfaction.md"):
                        total_files += 1

    # Warn if tasks in review/verified but meta absent
    warn = False
    if not meta_exists:
        for tasks_dir in [workspace / "tasks" / "review", workspace / "tasks" / "verified"]:
            if tasks_dir.exists():
                items = [f for f in tasks_dir.iterdir() if f.suffix == ".md"]
                if items:
                    warn = True
                    break

    return {
        "directories": directories,
        "total_files": total_files,
        "meta_exists": meta_exists,
        "warn": warn,
    }


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
        "specs/factory-internal",
        "tasks/research", "tasks/research-done", "tasks/building",
        "tasks/review", "tasks/verified", "tasks/failed", "tasks/decisions",
        "tasks/resolved", "tasks/maintenance",
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


# Model mapping for backend switching.
# Each anthropic model tier maps to a kimi equivalent.
_BACKEND_MODEL_MAP: dict[str, dict[str, str]] = {
    "to_kimi": {
        "claude-opus-4-6": "kimi-code/kimi-for-coding",
        "claude-sonnet-4-5": "kimi-code/kimi-for-coding",
        "claude-haiku-4-5": "kimi-code/kimi-for-coding",
    },
    "to_anthropic": {
        "kimi-code/kimi-for-coding": "claude-opus-4-6",
    },
}

# Store original anthropic models so `factory backend default` can restore them.
# Keyed by agent name → original model string.
_ORIGINAL_MODELS_FILE = ".factory-original-models.yaml"


@main.command()
@click.argument("backend", type=click.Choice(["kimi", "default"]))
def backend(backend: str) -> None:
    """Switch all agents between kimi and anthropic backends.

    \b
        factory backend kimi      # switch all agents to kimi-cli
        factory backend default   # restore all agents to anthropic (original models)
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    workspace = config.workspace
    agents_file = workspace / "agents.yaml"
    originals_file = workspace / _ORIGINAL_MODELS_FILE

    # Use line-level text replacement to preserve formatting, comments, and structure.
    text = agents_file.read_text()
    raw = yaml.safe_load(text)

    if backend == "kimi":
        # Save originals before switching
        originals = {}
        for name, agent_def in raw["agents"].items():
            originals[name] = {
                "model": agent_def.get("model", ""),
                "provider": agent_def.get("provider", "anthropic"),
            }
        originals_file.write_text(yaml.dump(originals, default_flow_style=False))

        # Replace provider and model lines in-place
        for name, agent_def in raw["agents"].items():
            old_model = agent_def.get("model", "")
            new_model = _BACKEND_MODEL_MAP["to_kimi"].get(old_model, "kimi-code/kimi-for-coding")
            text = text.replace(
                f"    model: {old_model}\n    provider: anthropic",
                f"    model: {new_model}\n    provider: kimi",
                1,
            )
            console.print(f"  {name}: anthropic/{old_model} → kimi/{new_model}")

    elif backend == "default":
        if originals_file.exists():
            originals = yaml.safe_load(originals_file.read_text()) or {}
        else:
            originals = {}

        for name, agent_def in raw["agents"].items():
            old_model = agent_def.get("model", "")
            old_provider = agent_def.get("provider", "kimi")
            if name in originals:
                new_model = originals[name]["model"]
                new_provider = originals[name]["provider"]
            else:
                new_model = old_model
                new_provider = "anthropic"

            text = text.replace(
                f"    model: {old_model}\n    provider: {old_provider}",
                f"    model: {new_model}\n    provider: {new_provider}",
                1,
            )
            console.print(f"  {name}: → {new_provider}/{new_model}")

    agents_file.write_text(text)
    console.print(f"\n[green]Backend switched to {backend}[/green]")

    # Validate the new config
    from .llm import validate_providers
    new_config = load_config()
    for warn in validate_providers(new_config):
        console.print(f"  [yellow]⚠  {warn}[/yellow]")


@main.command(name="init-project")
@click.option("--workspace", "-w", type=click.Path(), help="Factory workspace path (auto-detected if omitted)")
def init_project(workspace: str | None) -> None:
    """Register the current directory as a factory project.

    Writes a .factory marker file pointing to the factory workspace.
    After this, all factory commands work from within this directory.
    """
    project_dir = Path.cwd()
    marker = project_dir / ".factory"

    if marker.is_file():
        existing = yaml.safe_load(marker.read_text()) or {}
        console.print(f"Already registered. workspace: {existing.get('workspace')}")
        return

    # Resolve factory workspace
    if workspace:
        ws = Path(workspace).resolve()
    else:
        try:
            ws = find_workspace()
        except FileNotFoundError:
            console.print(
                "[red]Error:[/red] Cannot auto-detect factory workspace. "
                "Pass --workspace or set FACTORY_WORKSPACE."
            )
            sys.exit(1)

    if not (ws / "agents.yaml").exists():
        console.print(f"[red]Error:[/red] No agents.yaml at {ws}")
        sys.exit(1)

    marker.write_text(yaml.dump({"workspace": str(ws)}, default_flow_style=False))
    console.print(f"[green]Registered project:[/green] {project_dir.name}")
    console.print(f"  workspace: {ws}")
    console.print(f"  marker: {marker}")


@main.command()
@click.option("--max-steps", type=int, default=0, help="Stop after N agent runs (0 = unlimited)")
def start(max_steps: int) -> None:
    """Automated pipeline loop — dispatches agents until idle or gated.

    Checks pipeline state, dispatches the next agent in priority order
    (downstream-first), runs post-execution passes, then repeats.

    Stops when:
    - Pipeline is idle (nothing to do)
    - A gate is hit (unresolved decisions, critical/high observations)
    - An agent crashes or times out
    - A rebuild hits the retry limit
    - --max-steps limit reached

    \b
    Examples:
        factory start               # run until idle or gated
        factory start --max-steps 3 # run at most 3 agent dispatches
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    workspace = config.workspace

    # Startup validation
    from .llm import validate_providers
    for warn in validate_providers(config):
        console.print(f"  [yellow]⚠  {warn}[/yellow]")

    console.print("[bold]Factory pipeline starting[/bold]")

    step = 0
    while True:
        if max_steps > 0 and step >= max_steps:
            console.print(f"\n[dim]Reached --max-steps limit ({max_steps}). Stopping.[/dim]")
            break

        dispatch = _compute_next_dispatch(workspace, config)
        if dispatch is None:
            console.print("\n[bold]Pipeline idle or gated.[/bold]")
            print_pipeline_next("", workspace)
            break

        agent, spec_name_d, dispatch_type, message = dispatch

        # --- Handle auto-promote (no agent invocation) ---
        if dispatch_type == "auto-promote":
            fi_dir = workspace / "specs" / "factory-internal"
            matches, err = _resolve_factory_internal(fi_dir, spec_name_d)
            if matches:
                fi_file = matches[0]
                item = _parse_factory_internal_file(fi_file)
                slug = item.get("slug", fi_file.stem)
                obs_text = item.get("observation", "")

                # Write to inbox
                inbox_file = workspace / "specs" / "inbox" / f"{slug}.md"
                inbox_file.write_text(
                    f"# {slug}\n\n"
                    f"## What I'm Seeing\n{obs_text}\n\n"
                    f"## What I Want to See\nThis observation should be addressed.\n"
                )

                # Update factory-internal status
                now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                old_text = fi_file.read_text()
                new_text = old_text.replace(
                    "- status: open",
                    f"- status: promoted\n- promoted_to: specs/inbox/{slug}.md\n- promoted_at: {now}",
                    1,
                )
                fi_file.write_text(new_text)

                console.print(f"\n[bold]Auto-promoted:[/bold] {slug} → specs/inbox/")

                # Commit
                subprocess.run(
                    ["git", "add", str(inbox_file), str(fi_file)],
                    cwd=workspace, capture_output=True,
                )
                subprocess.run(
                    ["git", "commit", "-m",
                     f"Auto-promote low-severity observation: {slug}\n\n"
                     f"Factory start loop promoted {fi_file.name} to specs/inbox/."],
                    cwd=workspace, capture_output=True, text=True,
                )
            continue  # Don't increment step — no agent invocation

        # --- Handle rebuild (prep then builder) ---
        if dispatch_type == "rebuild":
            exit_code, rebuild_msg = rebuild_task(workspace, spec_name_d)
            if exit_code != 0:
                console.print(f"[red]Rebuild prep failed:[/red] {rebuild_msg}")
                break
            console.print(f"[green]Rebuild triggered:[/green] {spec_name_d}")
            subprocess.run(
                ["git", "add",
                 f"specs/ready/{spec_name_d}.md",
                 f"specs/ready/{spec_name_d}.rebuild.md",
                 "tasks/failed/"],
                cwd=workspace, capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m",
                 f"Trigger rebuild: {spec_name_d} (automated via factory start)"],
                cwd=workspace, capture_output=True, text=True,
            )
            # Continue to next iteration — builder will pick up the ready spec
            continue

        # --- Handle docs (directed librarian) ---
        if dispatch_type == "docs":
            # Build the docs context (same as the docs command)
            context_parts = [f"Update documentation for completed spec: {spec_name_d}\n"]
            spec_file = workspace / "specs" / "archive" / f"{spec_name_d}.md"
            if spec_file.exists():
                context_parts.append(f"--- Archived spec ---\n{spec_file.read_text()}\n")
            task_file = workspace / "tasks" / "verified" / f"{spec_name_d}.md"
            if task_file.exists():
                context_parts.append(f"--- Verified task ---\n{task_file.read_text()}\n")
            notes_file = workspace / "tasks" / "verified" / f"{spec_name_d}.builder-notes.md"
            if not notes_file.exists():
                notes_file = workspace / "tasks" / "review" / f"{spec_name_d}.builder-notes.md"
            if notes_file.exists():
                context_parts.append(f"--- Builder notes ---\n{notes_file.read_text()}\n")
            research_done = workspace / "tasks" / "research-done"
            if research_done.exists():
                for brief in sorted(research_done.glob("*.md")):
                    if spec_name_d in brief.stem:
                        context_parts.append(f"--- Research: {brief.name} ---\n{brief.read_text()}\n")
            dec_file = workspace / "tasks" / "decisions" / f"{spec_name_d}.md"
            if dec_file.exists():
                context_parts.append(f"--- Decisions ---\n{dec_file.read_text()}\n")
            for subdir in ["failures", "corrections", "discoveries"]:
                learn_dir = workspace / "learnings" / subdir
                if learn_dir.exists():
                    for f in sorted(learn_dir.glob(f"*{spec_name_d}*")):
                        context_parts.append(f"--- Learning ({subdir}): {f.name} ---\n{f.read_text()}\n")
            context_parts.append(
                "Review the above completed work. Update:\n"
                "1. memory/shared/KNOWLEDGE.md — if new conventions or decisions were established\n"
                "2. memory/shared/PROJECTS.md — if a project status changed\n"
                "3. skills/ — if patterns emerged that should become shared skills\n"
                "4. learnings/ — if the work produced insights not yet captured\n"
                "Only update what's warranted. Don't create entries for trivial changes."
            )
            message = "\n".join(context_parts)
            agent = "librarian"

        # --- Handle advance (context-aware spec progression) ---
        if dispatch_type == "advance":
            spec_file = _resolve_spec_file(workspace, spec_name_d)
            if spec_file is None:
                console.print(f"[red]Error:[/red] Cannot find spec {spec_name_d} to advance")
                break
            stage = spec_file.parent.name
            spec_content = spec_file.read_text()
            context_parts = [f"Advance this spec: {spec_name_d} (currently in {stage}/)\n"]
            context_parts.append(f"--- {spec_file.name} ---\n{spec_content}\n")
            research_done = workspace / "tasks" / "research-done"
            if research_done.exists():
                for brief in sorted(research_done.glob("*.md")):
                    if spec_name_d in brief.stem or brief.stem.startswith("spec-"):
                        context_parts.append(f"--- Research brief: {brief.name} ---\n{brief.read_text()}\n")
            dec_file = workspace / "tasks" / "decisions" / f"{spec_name_d}.md"
            if dec_file.exists():
                context_parts.append(f"--- Decisions: {dec_file.name} ---\n{dec_file.read_text()}\n")
            context_parts.append(
                "Incorporate the research findings and resolved decisions into the spec. "
                "If the spec is complete, move it to specs/ready/."
            )
            message = "\n".join(context_parts)
            agent = "spec"

        # --- Dispatch the agent ---
        if agent not in config.agents:
            console.print(f"[red]Error:[/red] Agent '{agent}' not configured")
            break

        result, success = _dispatch_agent(config, agent, message, f"{dispatch_type} {spec_name_d}")
        step += 1

        if not success:
            console.print(f"\n[red]Agent error — pipeline stopped.[/red]")
            _send_whatsapp(
                workspace, "factory-start",
                f"Pipeline stopped: {agent} error during {dispatch_type} {spec_name_d}",
                [],
            )
            break

        # Post-dispatch state transitions
        if dispatch_type == "docs":
            # Docs consumed the verified task — remove it so the loop doesn't retry.
            # The verification report is preserved in specs/archive/ and runs/.
            git_files = []
            for suffix in [".md", ".builder-notes.md"]:
                vf = workspace / "tasks" / "verified" / f"{spec_name_d}{suffix}"
                if vf.exists():
                    vf.unlink()
                    git_files.append(str(vf.relative_to(workspace)))
            if git_files:
                subprocess.run(
                    ["git", "add"] + git_files,
                    cwd=workspace, capture_output=True,
                )
                subprocess.run(
                    ["git", "commit", "-m",
                     f"Clear verified task: {spec_name_d} (docs completed)"],
                    cwd=workspace, capture_output=True, text=True,
                )
                console.print(f"  [dim]Cleared tasks/verified/{spec_name_d} (docs done)[/dim]")

    # Final status
    console.print()
    console.print(f"[dim]Pipeline loop completed after {step} agent dispatch{'es' if step != 1 else ''}.[/dim]")

    # Send summary WhatsApp
    next_actions = _compute_next_actions(workspace)
    _send_whatsapp(
        workspace, "factory-start",
        f"Pipeline loop completed ({step} step{'s' if step != 1 else ''})",
        next_actions,
    )


@main.command()
@click.argument("spec_name")
def advance(spec_name: str) -> None:
    """Advance a spec that has unblocking context (research, decisions).

    Determines the right agent and constructs a directed message with
    all available context: research briefs, resolved decisions, and
    the current spec content.

        factory advance multi-cli-backend-support
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    workspace = config.workspace

    # Find the spec
    spec_file = _resolve_spec_file(workspace, spec_name)
    if spec_file is None:
        console.print(f"[red]Error:[/red] No spec '{spec_name}' found in inbox/, drafting/, or ready/")
        sys.exit(1)

    stage = spec_file.parent.name
    spec_content = spec_file.read_text()

    # Determine which agent should handle it based on stage
    if stage in ("inbox", "drafting"):
        agent = "spec"
    elif stage == "ready":
        agent = "builder"
    else:
        console.print(f"[red]Error:[/red] Spec in unexpected stage: {stage}")
        sys.exit(1)

    # Gather unblocking context
    context_parts = [f"Advance this spec: {spec_name} (currently in {stage}/)\n"]
    context_parts.append(f"--- {spec_file.name} ---\n{spec_content}\n")

    # Research briefs
    research_done = workspace / "tasks" / "research-done"
    if research_done.exists():
        for brief in sorted(research_done.glob("*.md")):
            if spec_name in brief.stem or brief.stem.startswith("spec-"):
                context_parts.append(f"--- Research brief: {brief.name} ---\n{brief.read_text()}\n")

    # Resolved decisions
    dec_file = workspace / "tasks" / "decisions" / f"{spec_name}.md"
    if dec_file.exists():
        context_parts.append(f"--- Decisions: {dec_file.name} ---\n{dec_file.read_text()}\n")

    if stage in ("inbox", "drafting"):
        context_parts.append(
            "Incorporate the research findings and resolved decisions into the spec. "
            "If the spec is complete, move it to specs/ready/."
        )
    elif stage == "ready":
        context_parts.append(
            "Implement the spec. Research and decisions are provided for context."
        )

    message = "\n".join(context_parts)

    # Delegate to the run command logic
    agent_config = config.agents[agent]
    trigger = "message"

    run_logger = RunLogger(
        workspace=config.workspace,
        agent_name=agent,
        trigger=trigger,
        model=agent_config.model,
    )

    console.print(f"[bold]Advancing {spec_name}[/bold] via {agent} ({agent_config.model})")
    console.print(f"  Stage: {stage}/")
    console.print(f"  Run ID: {run_logger.run_id}")

    from .llm import run_agent as _run_agent

    try:
        result = _run_agent(
            config=config,
            agent_config=agent_config,
            message=message,
            is_heartbeat=False,
            run_logger=run_logger,
        )

        if result.strip().upper() == "NO_REPLY":
            console.print(f"  [dim]Agent responded: NO_REPLY[/dim]")
        else:
            console.print(f"\n[bold green]Agent response:[/bold green]")
            console.print(result)

        console.print(f"\n[dim]Run logged to runs/{run_logger.run_id}/[/dim]")
        print_pipeline_next(agent, config.workspace)

        # Post-execution kernel passes
        for line in run_spec_pipeline_cleanup(config.workspace):
            console.print(f"  [dim]{line}[/dim]")
        for line in run_task_review_cleanup(config.workspace):
            console.print(f"  [dim]{line}[/dim]")
        for line in run_research_cleanup(config.workspace):
            console.print(f"  [dim]{line}[/dim]")
        decision_log = run_decision_monitor(config.workspace, agent)
        for line in decision_log:
            if "hard gate" in line:
                console.print(f"  [yellow]{line}[/yellow]")
            else:
                console.print(f"  [dim]{line}[/dim]")

        # Observation extraction safety net
        obs_log = extract_surfaced_observations(config.workspace, agent, result)
        for line in obs_log:
            console.print(f"  [yellow]{line}[/yellow]")

        # Promote needs.md observation entries to factory-internal
        promo_log = promote_needs_observations(config.workspace, agent)
        for line in promo_log:
            console.print(f"  [dim]{line}[/dim]")

        # Factory-internal GC pass
        fi_gc_log = cleanup_factory_internal(config.workspace)
        for line in fi_gc_log:
            console.print(f"  [dim]{line}[/dim]")

        # One-time migration (idempotent after first run)
        mig_log = run_factory_internal_migration(config.workspace)
        for line in mig_log:
            console.print(f"  {line}")

        # WhatsApp notification
        if result.strip().upper() != "NO_REPLY":
            summary = result.strip()
            if len(summary) > 500:
                summary = summary[:497] + "..."
            next_actions = _compute_next_actions(config.workspace)
            _send_whatsapp(config.workspace, agent, summary, next_actions)

    except Exception as e:
        console.print(f"[red]Error during advance:[/red] {e}")
        run_logger.log_outcome(f"ERROR: {e}")
        sys.exit(1)


@main.command()
@click.argument("agent")
@click.argument("spec_name", required=False)
@click.option("--task", type=click.Path(exists=True), help="Task file to assign")
@click.option("--message", "-m", type=str, help="Free text message for the agent")
def run(agent: str, spec_name: str | None, task: str | None, message: str | None) -> None:
    """Invoke an agent. Heartbeat mode if no --task or --message given.

    Optionally pass a SPEC_NAME to direct the agent to a specific spec:

        factory run spec multi-cli-backend-support
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    if spec_name:
        # Resolve the spec file and inject as a directed message
        spec_file = _resolve_spec_file(config.workspace, spec_name)
        if spec_file is None:
            console.print(
                f"[red]Error:[/red] No spec '{spec_name}' found in inbox/, drafting/, or ready/"
            )
            sys.exit(1)
        stage = spec_file.parent.name
        message = (
            f"Work on this specific spec: {spec_name} (currently in {stage}/)\n\n"
            f"--- {spec_file.name} ---\n{spec_file.read_text()}"
        )

    if agent not in config.agents:
        console.print(
            f"[red]Error:[/red] Unknown agent '{agent}'. "
            f"Available: {', '.join(config.agents.keys())}"
        )
        sys.exit(1)

    agent_config = config.agents[agent]

    # Startup validation: warn if any provider's CLI binary is missing.
    # Missing binaries are warnings only — agents with working backends run normally.
    from .llm import validate_providers
    for warn in validate_providers(config):
        console.print(f"  [yellow]⚠  {warn}[/yellow]")

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

    console.print(f"[bold]Running {agent}[/bold] ({agent_config.model}, provider: {agent_config.provider})")
    console.print(f"  Trigger: {trigger}")
    console.print(f"  Run ID: {run_logger.run_id}")

    # Import and run
    from .llm import run_agent
    from .context import build_context_bar, estimate_tokens, MODEL_CONTEXT_WINDOWS

    # Pre-verification warning: alert when scenario holdouts are absent
    if agent == "verifier":
        scenario_warn = check_scenario_warning(config.workspace)
        if scenario_warn:
            console.print(f"  [yellow]Warning:[/yellow] {scenario_warn}")

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

        # Post-execution: research request cleanup (runs after every agent)
        research_cleanup_log = run_research_cleanup(config.workspace)
        for line in research_cleanup_log:
            console.print(f"  [dim]{line}[/dim]")

        # Post-execution: decision monitor (spec and builder agents)
        decision_log = run_decision_monitor(config.workspace, agent)
        for line in decision_log:
            if "hard gate" in line:
                console.print(f"  [yellow]{line}[/yellow]")
            else:
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

        # Post-execution: observation extraction safety net
        obs_log = extract_surfaced_observations(config.workspace, agent, result)
        for line in obs_log:
            console.print(f"  [yellow]{line}[/yellow]")

        # Post-execution: promote needs.md observation entries to factory-internal
        promo_log = promote_needs_observations(config.workspace, agent)
        for line in promo_log:
            console.print(f"  [dim]{line}[/dim]")

        # Post-execution: factory-internal GC pass
        fi_gc_log = cleanup_factory_internal(config.workspace)
        for line in fi_gc_log:
            console.print(f"  [dim]{line}[/dim]")

        # Post-execution: one-time migration (idempotent after first run)
        mig_log = run_factory_internal_migration(config.workspace)
        for line in mig_log:
            console.print(f"  {line}")

        # Post-execution: WhatsApp notification (skip NO_REPLY heartbeats)
        if result.strip().upper() != "NO_REPLY":
            # Build a concise summary from the agent response
            summary_lines = result.strip().split("\n")
            # Take first ~500 chars as summary
            summary = "\n".join(summary_lines)
            if len(summary) > 500:
                summary = summary[:497] + "..."
            next_actions = _compute_next_actions(config.workspace)
            _send_whatsapp(config.workspace, agent, summary, next_actions)

    except Exception as e:
        console.print(f"[red]Error during agent run:[/red] {e}")
        run_logger.log_outcome(f"ERROR: {e}")
        sys.exit(1)


@main.command()
def status() -> None:
    """Show factory status: agents, pipeline, and next actions."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    workspace = config.workspace
    runs_dir = workspace / "runs"

    # ── Agents ──
    lines: list[str] = []
    for name, agent in config.agents.items():
        age, no_reply = _agent_last_run(runs_dir, name)
        model = _model_short(agent.model)
        dot = "[green]●[/green]" if age != "never" else "[dim]○[/dim]"
        suffix = "  [dim](idle)[/dim]" if no_reply else ""
        lines.append(f"  {dot} {name:<14} {model:<8} {age}{suffix}")

    agent_block = "\n".join(lines)

    # ── Pipeline (non-empty only) ──
    pipeline_dirs = [
        ("specs/inbox", "inbox"),
        ("specs/drafting", "drafting"),
        ("specs/ready", "ready"),
        ("tasks/research", "research"),
        ("tasks/building", "building"),
        ("tasks/review", "review"),
        ("tasks/verified", "verified"),
        ("tasks/failed", "failed"),
        ("tasks/decisions", "decisions"),
    ]

    pipeline_lines: list[str] = []
    for rel_path, label in pipeline_dirs:
        count, names = _count_dir(workspace, rel_path)
        if count > 0:
            name_str = ", ".join(names[:3])
            if count > 3:
                name_str += f" (+{count - 3})"
            pipeline_lines.append(
                f"  [yellow]▸[/yellow] {label:<14} [yellow]{count}[/yellow]  {name_str}"
            )

    # Decisions and needs inline
    dec_count, _ = _count_dir(workspace, "tasks/decisions")
    needs_entries = parse_needs_entries(workspace)
    open_needs = [e for e in needs_entries if e["status"] == "open" and e["category"] != "observation"]

    status_notes: list[str] = []
    if dec_count > 0:
        # Count hard gates specifically
        hard_count = 0
        auto_count = 0
        for dec_file in sorted((workspace / "tasks" / "decisions").glob("*.md")):
            text = dec_file.read_text()
            hard_count += text.count("awaiting-operator")
            auto_count += text.count("auto-resolved")
        if hard_count > 0:
            status_notes.append(f"[yellow]{hard_count} decision(s) awaiting operator[/yellow]")
        if auto_count > 0:
            status_notes.append(f"[dim]{auto_count} auto-resolved[/dim]")
    if open_needs:
        status_notes.append(f"[yellow]{len(open_needs)} need(s) pending[/yellow]")

    if not pipeline_lines and not status_notes:
        pipeline_block = "  [dim]Pipeline empty.[/dim]"
    else:
        parts = []
        if pipeline_lines:
            parts.append("\n".join(pipeline_lines))
        if status_notes:
            parts.append("  " + "  ".join(status_notes))
        pipeline_block = "\n".join(parts)

    # ── Factory Internal ──
    fi_items = _list_factory_internal(workspace, include_all=False)
    fi_block = ""
    if fi_items:
        by_sev: dict[str, list[dict]] = {"critical": [], "high": [], "low": []}
        for item in fi_items:
            by_sev.setdefault(item["severity"], []).append(item)
        fi_lines: list[str] = [
            f"\n[bold]Factory Internal[/bold] ({len(fi_items)} open):"
        ]
        for sev in ("critical", "high", "low"):
            sev_items = by_sev.get(sev, [])
            if not sev_items:
                continue
            slugs = ", ".join(i["slug"] for i in sev_items[:3])
            if len(sev_items) > 3:
                slugs += f" (+{len(sev_items) - 3})"
            color = "red" if sev == "critical" else "yellow" if sev == "high" else "dim"
            fi_lines.append(
                f"  [yellow]▸[/yellow] [{color}]{sev:<8}[/{color}]"
                f"  {len(sev_items)}   {slugs}"
            )
        fi_block = "\n".join(fi_lines)

    # ── Next actions ──
    actions = _compute_next_actions(workspace)
    if actions:
        next_lines = [f"  → [bold]{a}[/bold]" for a in actions[:3]]
        if len(actions) > 3:
            next_lines.append(f"  [dim]  ...and {len(actions) - 3} more[/dim]")
        next_block = "\n".join(next_lines)
    else:
        next_block = "  [dim]Nothing to do.[/dim]"

    # ── Project context ──
    project_line = ""
    if config.project_name:
        project_line = f"\n[dim]  project: {config.project_name} ({config.project_dir})[/dim]\n"

    # ── Render ──
    output = Text.from_markup(
        f"{agent_block}\n"
        f"{project_line}"
        f"\n[bold]Pipeline[/bold]\n"
        f"{pipeline_block}"
        f"{fi_block}\n"
        f"\n[bold]Next[/bold]\n"
        f"{next_block}"
    )
    console.print(Panel(output, title="[bold]Factory[/bold]", border_style="dim"))

    # Run one-time migration on factory status invocation
    mig_log = run_factory_internal_migration(workspace)
    for line in mig_log:
        console.print(f"  {line}")


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
            ("decisions", "tasks/decisions"),
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


@main.command()
@click.argument("spec_name")
def docs(spec_name: str) -> None:
    """Update documentation after a spec completes the pipeline.

    Gathers the archived spec, verified task, research briefs, decisions,
    and learnings, then sends the librarian to update shared knowledge,
    skills, and memory.

        factory docs hello-world-python
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    workspace = config.workspace
    agent = "librarian"

    if agent not in config.agents:
        console.print(f"[red]Error:[/red] No librarian agent configured")
        sys.exit(1)

    agent_config = config.agents[agent]

    # Gather all context for the completed work
    context_parts = [f"Update documentation for completed spec: {spec_name}\n"]

    # Archived spec
    spec_file = workspace / "specs" / "archive" / f"{spec_name}.md"
    if spec_file.exists():
        context_parts.append(f"--- Archived spec ---\n{spec_file.read_text()}\n")

    # Verified task
    task_file = workspace / "tasks" / "verified" / f"{spec_name}.md"
    if task_file.exists():
        context_parts.append(f"--- Verified task ---\n{task_file.read_text()}\n")

    # Builder notes
    notes_file = workspace / "tasks" / "verified" / f"{spec_name}.builder-notes.md"
    if not notes_file.exists():
        notes_file = workspace / "tasks" / "review" / f"{spec_name}.builder-notes.md"
    if notes_file.exists():
        context_parts.append(f"--- Builder notes ---\n{notes_file.read_text()}\n")

    # Research briefs
    research_done = workspace / "tasks" / "research-done"
    if research_done.exists():
        for brief in sorted(research_done.glob("*.md")):
            if spec_name in brief.stem:
                context_parts.append(f"--- Research: {brief.name} ---\n{brief.read_text()}\n")

    # Decisions
    dec_file = workspace / "tasks" / "decisions" / f"{spec_name}.md"
    if dec_file.exists():
        context_parts.append(f"--- Decisions ---\n{dec_file.read_text()}\n")

    # Related learnings
    for subdir in ["failures", "corrections", "discoveries"]:
        learn_dir = workspace / "learnings" / subdir
        if learn_dir.exists():
            for f in sorted(learn_dir.glob(f"*{spec_name}*")):
                context_parts.append(f"--- Learning ({subdir}): {f.name} ---\n{f.read_text()}\n")

    context_parts.append(
        "Review the above completed work. Update:\n"
        "1. memory/shared/KNOWLEDGE.md — if new conventions or decisions were established\n"
        "2. memory/shared/PROJECTS.md — if a project status changed\n"
        "3. skills/ — if patterns emerged that should become shared skills\n"
        "4. learnings/ — if the work produced insights not yet captured\n"
        "Only update what's warranted. Don't create entries for trivial changes."
    )

    message = "\n".join(context_parts)

    run_logger = RunLogger(
        workspace=workspace,
        agent_name=agent,
        trigger="message",
        model=agent_config.model,
    )

    console.print(f"[bold]Updating docs for {spec_name}[/bold] via {agent} ({agent_config.model})")
    console.print(f"  Run ID: {run_logger.run_id}")

    from .llm import run_agent as _run_agent

    try:
        result = _run_agent(
            config=config,
            agent_config=agent_config,
            message=message,
            is_heartbeat=False,
            run_logger=run_logger,
        )

        if result.strip().upper() == "NO_REPLY":
            console.print(f"  [dim]Librarian: nothing to update[/dim]")
        else:
            console.print(f"\n[bold green]Librarian response:[/bold green]")
            console.print(result)

        console.print(f"\n[dim]Run logged to runs/{run_logger.run_id}/[/dim]")
        print_pipeline_next(agent, workspace)

        # Clear verified task — docs consumed it
        git_files = []
        for suffix in [".md", ".builder-notes.md"]:
            vf = workspace / "tasks" / "verified" / f"{spec_name}{suffix}"
            if vf.exists():
                vf.unlink()
                git_files.append(str(vf.relative_to(workspace)))
        if git_files:
            subprocess.run(
                ["git", "add"] + git_files,
                cwd=workspace, capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m",
                 f"Clear verified task: {spec_name} (docs completed)"],
                cwd=workspace, capture_output=True, text=True,
            )
            console.print(f"  [dim]Cleared tasks/verified/{spec_name} (docs done)[/dim]")

        # WhatsApp notification
        if result.strip().upper() != "NO_REPLY":
            summary = result.strip()
            if len(summary) > 500:
                summary = summary[:497] + "..."
            next_actions = _compute_next_actions(workspace)
            _send_whatsapp(workspace, agent, summary, next_actions)

    except Exception as e:
        console.print(f"[red]Error during docs update:[/red] {e}")
        run_logger.log_outcome(f"ERROR: {e}")
        sys.exit(1)


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


@main.command(name="cleanup-research")
@click.option("--dry-run", is_flag=True, default=False, help="Show what would be cleaned without deleting.")
def cleanup_research_cmd(dry_run: bool) -> None:
    """Remove stale research requests that have completed deliverables.

    A tasks/research/ file is stale when the same filename exists in
    tasks/research-done/ (the completed brief).
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    log_lines = run_research_cleanup(config.workspace, dry_run=dry_run)

    if not log_lines:
        console.print("[dim]Research pipeline is clean — no stale requests found.[/dim]")
        return

    prefix = "[dry-run] Would clean" if dry_run else "Cleaned"
    for line in log_lines:
        display = line.replace("Cleaned stale research request:", f"{prefix}:")
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


def parse_decision_entries(decision_file: Path) -> list[dict]:
    """Parse structured ambiguity entries from a tasks/decisions/ file.

    Each entry starts with a ### heading and contains tagged fields
    (status, reversibility, impact) and an Options section.

    Returns a list of dicts with keys: id, status, reversibility, impact,
    options, recommendation, context.
    """
    if not decision_file.exists():
        return []

    text = decision_file.read_text()
    # Split on ### headings (level 3)
    blocks = re.split(r"(?=^### )", text, flags=re.MULTILINE)
    entries: list[dict] = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        heading_match = re.match(r"^### (.+)", block)
        if not heading_match:
            continue

        raw_heading = heading_match.group(1).strip()
        # Extract the numeric prefix (e.g. "7.1") as the short ID for matching
        id_match = re.match(r"^(\d+\.\d+)", raw_heading)
        entry_id = id_match.group(1) if id_match else raw_heading
        entry_title = raw_heading

        def get_field(field_name: str, _block: str = block) -> str | None:
            m = re.search(
                rf"^- {re.escape(field_name)}:\s*(.+)$", _block, re.MULTILINE
            )
            return m.group(1).strip() if m else None

        # Extract options section
        options_match = re.search(
            r"^(?:\*\*Options:\*\*|### Options)\s*\n(.*?)(?=^###|\*\*Recommendation|\Z)",
            block, re.MULTILINE | re.DOTALL,
        )
        options_text = options_match.group(1).strip() if options_match else None

        # Extract recommendation
        rec_match = re.search(
            r"\*\*Recommendation:\*\*\s*(.*?)(?=^###|\Z)",
            block, re.MULTILINE | re.DOTALL,
        )
        recommendation = rec_match.group(1).strip() if rec_match else None

        entries.append({
            "id": entry_id,
            "title": entry_title,
            "status": get_field("status") or "open",
            "reversibility": get_field("reversibility") or "unknown",
            "impact": get_field("impact") or "unknown",
            "options": options_text,
            "recommendation": recommendation,
            "context": get_field("context"),
        })

    # Deduplicate: if the Decision Monitor prepended status-only headers,
    # the same ID appears twice. Keep the one with the richest status
    # (awaiting-operator or auto-resolved or resolved over open).
    seen: dict[str, int] = {}
    deduped: list[dict] = []
    status_priority = {"resolved": 4, "auto-resolved": 3, "awaiting-operator": 2, "open": 1}
    for e in entries:
        eid = e["id"]
        prio = status_priority.get(e["status"], 0)
        if eid in seen:
            existing_idx = seen[eid]
            existing_prio = status_priority.get(deduped[existing_idx]["status"], 0)
            if prio > existing_prio:
                deduped[existing_idx] = e
        else:
            seen[eid] = len(deduped)
            deduped.append(e)

    return deduped


def resolve_decision(
    decision_file: Path, entry_id: str, answer: str
) -> tuple[int, str]:
    """Mark a decision entry as resolved with the operator's answer.

    Returns (exit_code, message):
    - 0 — success
    - 1 — entry not found or already resolved
    """
    if not decision_file.exists():
        return 1, f"Decision file not found: {decision_file}"

    text = decision_file.read_text()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # Find the entry block and replace its status.
    # Support prefix matching: --entry 7.1 matches "### 7.1 Governance hook gap..."
    pattern = re.compile(
        rf"(### {re.escape(entry_id)}[^\n]*\n.*?)(- status:\s*\S+)",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return 1, f"No entry found: {entry_id}"

    current_status = re.search(r"- status:\s*(\S+)", match.group(0))
    if current_status and current_status.group(1) not in ("open", "awaiting-operator"):
        return 1, f"Entry already resolved: {entry_id} (status: {current_status.group(1)})"

    # Replace status and add answer + timestamp
    new_status_block = (
        f"- status: resolved\n"
        f"- decided-by: operator\n"
        f"- decided-at: {now}\n"
        f"- answer: {answer}"
    )
    new_text = text[:match.start(2)] + new_status_block + text[match.end(2):]
    decision_file.write_text(new_text)
    return 0, f"Resolved: {entry_id} → {answer}"


@main.command()
@click.argument("spec_name", required=False)
@click.option("--answer", "-a", type=str, help="Answer for a specific entry (use with --entry).")
@click.option("--entry", "-e", type=str, help="Entry ID to resolve.")
@click.option("--override", is_flag=True, default=False, help="Override an auto-resolved decision.")
def decide(spec_name: str | None, answer: str | None, entry: str | None, override: bool) -> None:
    """Show or resolve decision requests in tasks/decisions/.

    Without arguments, lists all pending decisions across all specs.
    With SPEC_NAME, shows decisions for that spec.
    With --entry and --answer, resolves a specific decision.

    \\b
    Exit codes:
      0  Success
      1  Spec not found or entry not found
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    workspace = config.workspace
    decisions_dir = workspace / "tasks" / "decisions"

    if not decisions_dir.exists():
        console.print("[dim]No decisions pending.[/dim]")
        return

    # Resolve mode: answer a specific entry
    if spec_name and entry and answer:
        decision_file = decisions_dir / f"{spec_name}.md"
        if not decision_file.exists():
            console.print(f"[red]Error:[/red] No decision file: tasks/decisions/{spec_name}.md")
            sys.exit(1)

        exit_code, message = resolve_decision(decision_file, entry, answer)
        if exit_code == 0:
            console.print(f"[green]{message}[/green]")
            # Stage and commit
            subprocess.run(
                ["git", "add", "tasks/decisions/"],
                cwd=workspace,
                capture_output=True,
            )
            result = subprocess.run(
                ["git", "commit", "-m",
                 f"Operator decision: {spec_name} / {entry}\n\n"
                 f"Answer: {answer}"],
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

            # Check if all entries in this file are resolved
            remaining = [
                e for e in parse_decision_entries(decision_file)
                if e["status"] in ("open", "awaiting-operator")
            ]
            if not remaining:
                console.print(f"\n[green]All decisions resolved for {spec_name}.[/green]")
                console.print(f"  Next: [bold]factory run spec[/bold]")
            else:
                console.print(f"\n  {len(remaining)} decision(s) still pending for {spec_name}.")
        else:
            console.print(f"[red]Error:[/red] {message}")
            sys.exit(1)
        return

    # Display mode: show pending decisions
    decision_files = sorted(decisions_dir.glob("*.md"))
    if not decision_files:
        console.print("[dim]No decisions pending.[/dim]")
        return

    # Filter to specific spec if provided
    if spec_name:
        decision_files = [f for f in decision_files if f.stem == spec_name]
        if not decision_files:
            console.print(f"[red]Error:[/red] No decision file: tasks/decisions/{spec_name}.md")
            sys.exit(1)

    total_pending = 0
    total_auto = 0

    for df in decision_files:
        entries = parse_decision_entries(df)
        if not entries:
            continue

        console.print(f"\n[bold]{df.stem}[/bold]")

        for e in entries:
            status = e["status"]
            rev = e["reversibility"]
            impact = e["impact"]
            tag = f"[dim]rev:{rev} impact:{impact}[/dim]"

            if status in ("open", "awaiting-operator"):
                console.print(f"  [yellow]PENDING[/yellow]  {e['id']}  {tag}")
                if e["options"]:
                    for line in e["options"].splitlines():
                        console.print(f"    {line}")
                if e["recommendation"]:
                    console.print(f"    [dim]Rec: {e['recommendation']}[/dim]")
                total_pending += 1
            elif status == "auto-resolved":
                if override or spec_name:
                    console.print(f"  [green]AUTO[/green]     {e['id']}  {tag}")
                total_auto += 1
            else:
                if spec_name:
                    console.print(f"  [dim]RESOLVED[/dim]  {e['id']}  {tag}")

    console.print()
    if total_pending > 0:
        console.print(
            f"[yellow]{total_pending}[/yellow] decision(s) awaiting operator. "
            f"{total_auto} auto-resolved."
        )
        console.print("Resolve with: [bold]factory decide SPEC --entry ENTRY_ID --answer CHOICE[/bold]")
    else:
        console.print(f"All decisions resolved. {total_auto} were auto-resolved.")
        console.print("Next: [bold]factory run spec[/bold]")


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
@click.option(
    "--blockers-only",
    "blockers_only",
    is_flag=True,
    default=False,
    help="Show only blocker categories (permission-change, config-edit, manual-intervention, approval). "
         "Excludes observation entries.",
)
def needs(resolve_id: str | None, show_all: bool, blockers_only: bool) -> None:
    """Show or resolve human-action-needed entries across all agents.

    Reads memory/*/needs.md and displays open items grouped by category,
    sorted oldest-first within each category.

    Note: ``--blockers-only`` is retained for backward compatibility.
    Observation entries are now handled via ``factory triage`` and are
    excluded from this command regardless of flags.

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
    _ = blockers_only  # retained for backward compat; observations excluded regardless

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

    # Observations are now handled via `factory triage` (specs/factory-internal/).
    # Exclude them from needs display entirely.
    all_entries = [e for e in all_entries if e["category"] != "observation"]

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
        console.print("[dim]  (observations are in factory triage — run `factory triage --list`)[/dim]")
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

    def _print_entry(entry: dict) -> None:
        age = _format_age(entry["created"])
        eid = entry["id"]
        agent_label = entry["agent"]
        blocked = entry["blocked"] or "(no description)"
        status_tag = (
            ""
            if entry["status"] == "open"
            else f" [dim]\\[{entry['status']}][/dim]"
        )
        console.print(
            f"  [cyan]{eid:<44}[/cyan]  [dim]\\[{agent_label}, {age}][/dim]{status_tag}"
        )
        console.print(f"    {blocked}")

    # Blocker display: known categories in canonical order, then unknown extras
    # --blockers-only is retained for backward compatibility (observations are
    # already excluded, so the flag is now a no-op for observation filtering).
    known_blocker_keys = [k for k, _ in _CATEGORY_DISPLAY_ORDER]
    extra_keys = [k for k in categories if k not in known_blocker_keys]
    ordered_blocker_keys = known_blocker_keys + extra_keys

    for cat_key in ordered_blocker_keys:
        if cat_key not in categories:
            continue
        cat_entries = categories[cat_key]
        display_name = next(
            (name for k, name in _CATEGORY_DISPLAY_ORDER if k == cat_key),
            cat_key.replace("-", " ").title(),
        )
        console.print(f"[bold]{display_name}[/bold] ({len(cat_entries)}):")
        for entry in cat_entries:
            _print_entry(entry)
        console.print()


@main.command()
@click.argument("agent_name", required=False, metavar="AGENT")
def reflect(agent_name: str | None) -> None:
    """Invoke agents with a reflection prompt.

    Agents examine their own configuration, memory, and pipeline state,
    then write observations to memory/{agent}/needs.md.

    If AGENT is omitted, all agents are invoked sequentially in pipeline
    order: researcher, spec, builder, verifier, librarian, operator, reviewer.

    \b
    Exit codes:
      0   All invoked agents completed (some may have written NO_REPLY)
      1   Invalid agent name specified
      2   All invoked agents failed (none completed successfully)
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    workspace = config.workspace

    # Determine which agents to invoke
    if agent_name is not None:
        if agent_name not in config.agents:
            console.print(f"Unknown agent: {agent_name}")
            sys.exit(1)
        agents_to_run = [agent_name]
    else:
        # All agents in pipeline order, limited to those present in config
        agents_to_run = [a for a in PIPELINE_ORDER if a in config.agents]

    # Snapshot needs entry IDs before the reflection pass for delta counting
    pre_ids = _snapshot_needs_ids(workspace)

    from .llm import run_agent
    from .run_log import RunLogger

    n_ran = 0
    failed: list[str] = []

    for name in agents_to_run:
        agent_cfg = config.agents[name]
        console.print(f"\n[bold]Reflecting:[/bold] {name} ({agent_cfg.model})")

        # Build the agent's own YAML block from agents.yaml
        agent_yaml = _agent_yaml_block(workspace, name)

        # Optionally load the shared/agent-reflection skill to include inline
        reflection_skill_path = (
            workspace / "skills" / "shared" / "agent-reflection" / "SKILL.md"
        )
        skill_block = ""
        if reflection_skill_path.exists():
            skill_block = "\n\n" + reflection_skill_path.read_text()

        reflection_prompt = (
            "This is a reflection pass, not a heartbeat. You are being asked to examine "
            "yourself — your configuration, your recent work, your place in the pipeline — "
            "and surface observations for the human.\n\n"
            "Your current configuration from agents.yaml:\n"
            "---\n"
            f"{agent_yaml}"
            "---\n"
            f"{skill_block}\n\n"
            f"Load the `shared/agent-reflection` skill and follow its instructions. "
            f"Write your observations to memory/{name}/needs.md using the "
            "human-action-needed format with the appropriate category. "
            "If you have nothing to observe, write NO_REPLY and exit."
        )

        run_logger = RunLogger(
            workspace=workspace,
            agent_name=name,
            trigger="reflection",
            model=agent_cfg.model,
        )

        try:
            result = run_agent(
                config=config,
                agent_config=agent_cfg,
                message=reflection_prompt,
                is_heartbeat=False,
                run_logger=run_logger,
            )
            if result.strip().upper() == "NO_REPLY":
                console.print(f"  [dim]NO_REPLY — no observations.[/dim]")
            else:
                console.print(f"  [dim]Agent completed.[/dim]")
            n_ran += 1

            # Promote any observation entries this agent wrote during reflection
            promo_log = promote_needs_observations(workspace, name)
            for line in promo_log:
                console.print(f"  [dim]{line}[/dim]")

        except Exception as e:
            console.print(f"  [red]Failed:[/red] {e}")
            failed.append(name)

    # Snapshot needs entry IDs after the reflection pass and compute delta
    post_ids = _snapshot_needs_ids(workspace)
    new_count = len(post_ids - pre_ids)

    # Count promoted factory-internal items created during this pass
    fi_items = _list_factory_internal(workspace, include_all=False)
    fi_open_count = len(fi_items)

    # Summary output
    total = n_ran + len(failed)
    console.print()
    if failed:
        fail_str = ", ".join(failed)
        console.print(
            f"Reflection complete — {total} agents ran "
            f"({len(failed)} failed: {fail_str}), "
            f"{new_count} new observations written."
        )
    else:
        console.print(
            f"Reflection complete — {total} agents ran, "
            f"{new_count} new observations written."
        )

    if fi_open_count > 0:
        console.print(f"\n[dim]{fi_open_count} open observation(s) in factory triage — run `factory triage --list`[/dim]")

    # Exit code 2 if every invoked agent failed
    if failed and n_ran == 0:
        sys.exit(2)


@main.group()
def scenario() -> None:
    """Manage scenario holdout files for verification."""
    pass


@scenario.command(name="init-meta")
def scenario_init_meta() -> None:
    """Create the factory meta-scenario file at scenarios/meta/factory-itself.md.

    Idempotent — running when the file already exists prints its path and exits
    without modifying it, preserving any human edits.

    \b
    Exit code: 0 in all cases.
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    workspace = config.workspace
    meta_dir = workspace / "scenarios" / "meta"
    meta_file = meta_dir / "factory-itself.md"

    if meta_file.exists():
        console.print(f"Already exists: {meta_file.relative_to(workspace)}")
        return

    meta_dir.mkdir(parents=True, exist_ok=True)
    meta_file.write_text(_META_SCENARIO_CONTENT)
    console.print(f"Created {meta_file.relative_to(workspace)}")


@scenario.command(name="new")
@click.argument("project_name")
def scenario_new(project_name: str) -> None:
    """Create a scenario template for PROJECT_NAME at scenarios/{project-name}/_template.md.

    Idempotent — if the directory already exists, prints a message and does not
    overwrite any files.  If the directory exists but _template.md is missing,
    writes the template.

    \b
    Project name must match [a-z0-9][a-z0-9_-]* (lowercase, hyphens, underscores).
    Exit code: 1 if project-name is invalid, 0 otherwise.
    """
    if not _SCENARIO_PROJECT_NAME_RE.match(project_name):
        console.print(
            f"[red]Error:[/red] Invalid project name '{project_name}'. "
            "Must match [a-z0-9][a-z0-9_-]* (lowercase letters/digits, hyphens, underscores, "
            "no leading special characters)."
        )
        sys.exit(1)

    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    workspace = config.workspace
    project_dir = workspace / "scenarios" / project_name
    template_file = project_dir / "_template.md"

    if project_dir.exists() and template_file.exists():
        console.print(f"Already exists: scenarios/{project_name}/")
        return

    project_dir.mkdir(parents=True, exist_ok=True)
    template_file.write_text(_SCENARIO_TEMPLATE_CONTENT)
    console.print(f"Created scenarios/{project_name}/_template.md")


@scenario.command(name="list")
def scenario_list() -> None:
    """List all scenario directories with file counts and satisfaction status.

    \b
    Columns: Name, Scenarios, Satisfaction
    Exit code: 0 always.
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    workspace = config.workspace
    scenarios_dir = workspace / "scenarios"

    if not scenarios_dir.exists() or not any(scenarios_dir.iterdir()):
        console.print(
            "No scenario directories found. "
            "Run `factory scenario init-meta` to create the meta-scenario."
        )
        return

    subdirs = sorted(sub for sub in scenarios_dir.iterdir() if sub.is_dir())

    if not subdirs:
        console.print(
            "No scenario directories found. "
            "Run `factory scenario init-meta` to create the meta-scenario."
        )
        return

    table = Table()
    table.add_column("Name", style="bold")
    table.add_column("Scenarios", justify="right")
    table.add_column("Satisfaction")

    for sub in subdirs:
        # Display name: add [meta] label for the meta directory.
        # Use \[meta] to prevent Rich from treating it as markup.
        display_name = r"meta \[meta]" if sub.name == "meta" else sub.name

        # Count .md files excluding _template.md and satisfaction.md
        scenario_files = [
            f for f in sub.glob("*.md")
            if f.name not in ("_template.md", "satisfaction.md")
        ]
        count = len(scenario_files)

        # Satisfaction: check for satisfaction.md and its modification date
        sat_file = sub / "satisfaction.md"
        if sat_file.exists():
            mtime = datetime.fromtimestamp(sat_file.stat().st_mtime)
            satisfaction = f"✓ ({mtime.strftime('%Y-%m-%d')})"
        else:
            satisfaction = "—"

        table.add_row(display_name, str(count), satisfaction)

    console.print(table)


@main.command()
@click.argument("filename_or_slug", required=False, metavar="FILENAME_OR_SLUG")
@click.option("--list", "do_list", is_flag=True, default=False,
              help="List open observations.")
@click.option("--all", "show_all", is_flag=True, default=False,
              help="Include promoted and dismissed entries (with --list).")
@click.option("--promote", "do_promote", is_flag=True, default=False,
              help="Move observation to specs/inbox/ for pipeline processing.")
@click.option("--dismiss", "do_dismiss", is_flag=True, default=False,
              help="Mark observation as dismissed (requires --reason).")
@click.option("--reason", default=None,
              help="Reason for dismissal (required with --dismiss).")
def triage(
    filename_or_slug: str | None,
    do_list: bool,
    show_all: bool,
    do_promote: bool,
    do_dismiss: bool,
    reason: str | None,
) -> None:
    """Manage factory-internal observations.

    \b
    Usage:
      factory triage --list [--all]
      factory triage FILENAME_OR_SLUG --promote
      factory triage FILENAME_OR_SLUG --dismiss --reason "..."
      factory triage FILENAME_OR_SLUG

    FILENAME_OR_SLUG may be the full filename (e.g. 2026-02-25T0817-low-my-obs.md)
    or just the slug portion (e.g. my-obs).  If the slug matches multiple files,
    the command lists all matches and exits with code 1.

    \b
    Exit codes:
      0  Success
      1  Slug matches multiple files, file not found, or --dismiss without --reason
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    workspace = config.workspace
    fi_dir = workspace / "specs" / "factory-internal"

    # ── List mode ──
    if do_list or (not filename_or_slug and not do_promote and not do_dismiss):
        items = _list_factory_internal(workspace, include_all=show_all)
        if not items:
            if show_all:
                console.print("[dim]No factory-internal observations.[/dim]")
            else:
                console.print("[dim]No open factory-internal observations.[/dim]")
                console.print("[dim]  Use --all to include promoted and dismissed.[/dim]")
            return

        scope = "all" if show_all else "open"
        console.print(f"\n[bold]Factory Internal[/bold] ({len(items)} {scope}):\n")
        for item in items:
            age = _format_age(item["created"])
            sev = item["severity"]
            color = "red" if sev == "critical" else "yellow" if sev == "high" else "dim"
            status_tag = (
                "" if item["status"] == "open"
                else f"  [dim][{item['status']}][/dim]"
            )
            first_line = item["observation"].split("\n")[0][:80]
            console.print(
                f"  [{color}]{sev:<8}[/{color}]  "
                f"[bold]{item['filename']}[/bold]{status_tag}"
            )
            console.print(f"    [dim]{item['source_agent']}, {age}[/dim]  {first_line}")
        console.print()
        return

    # ── File-targeted modes: require filename_or_slug ──
    if not filename_or_slug:
        console.print("[red]Error:[/red] FILENAME_OR_SLUG is required for --promote and --dismiss.")
        sys.exit(1)

    matches, err = _resolve_factory_internal(fi_dir, filename_or_slug)
    if err:
        console.print(f"[red]Error:[/red] {err}")
        sys.exit(1)
    if len(matches) > 1:
        console.print(
            f"[red]Error:[/red] Slug '{filename_or_slug}' matches multiple files:"
        )
        for m in matches:
            console.print(f"  {m.name}")
        sys.exit(1)

    target_file = matches[0]
    item = _parse_factory_internal_file(target_file)
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # ── Dismiss mode ──
    if do_dismiss:
        if not reason:
            console.print("[red]Error:[/red] --dismiss requires --reason.")
            sys.exit(1)

        content = target_file.read_text()
        # Update status and add dismissed metadata after the status line
        content = re.sub(
            r"^(- status:\s*)\S+",
            r"\g<1>dismissed",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        # Append dismissed metadata before ## Observation
        obs_pos = content.find("\n## Observation")
        dismissed_block = (
            f"\n- dismissed_reason: {reason}"
            f"\n- dismissed_at: {now}"
        )
        if obs_pos >= 0:
            content = content[:obs_pos] + dismissed_block + content[obs_pos:]
        else:
            content = content.rstrip() + dismissed_block + "\n"

        target_file.write_text(content)
        console.print(f"[green]Dismissed:[/green] {target_file.name}")
        console.print(f"  Reason: {reason}")

        subprocess.run(["git", "add", "specs/factory-internal/"], cwd=workspace, capture_output=True)
        result = subprocess.run(
            ["git", "commit", "-m",
             f"Dismiss factory-internal observation: {target_file.name}\n\n"
             f"Reason: {reason}"],
            cwd=workspace, capture_output=True, text=True,
        )
        if result.returncode == 0:
            console.print("  [dim]State committed to git.[/dim]")
        else:
            console.print(f"  [yellow]Warning:[/yellow] git commit failed: {result.stderr.strip()}")
        return

    # ── Promote mode ──
    if do_promote:
        inbox_dir = workspace / "specs" / "inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)

        slug = item["slug"]
        inbox_file = inbox_dir / f"{slug}.md"

        # Write raw intent to specs/inbox/
        obs_text = item["observation"]
        intent_content = (
            f"# {slug}\n\n"
            f"{obs_text}\n\n"
            f"## Source\n"
            f"Promoted from factory-internal observation: {target_file.name}\n"
            f"Source agent: {item['source_agent']}\n"
            f"Original severity: {item['severity']}\n"
        )
        inbox_file.write_text(intent_content)

        # Update factory-internal file: status → promoted
        content = target_file.read_text()
        content = re.sub(
            r"^(- status:\s*)\S+",
            r"\g<1>promoted",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        promoted_block = (
            f"\n- promoted_to: specs/inbox/{slug}.md"
            f"\n- promoted_at: {now}"
        )
        obs_pos = content.find("\n## Observation")
        if obs_pos >= 0:
            content = content[:obs_pos] + promoted_block + content[obs_pos:]
        else:
            content = content.rstrip() + promoted_block + "\n"
        target_file.write_text(content)

        console.print(f"[green]Promoted:[/green] {target_file.name}")
        console.print(f"  Intent written: specs/inbox/{slug}.md")

        subprocess.run(
            ["git", "add", "specs/factory-internal/", "specs/inbox/"],
            cwd=workspace, capture_output=True,
        )
        result = subprocess.run(
            ["git", "commit", "-m",
             f"Promote factory-internal observation to pipeline: {slug}\n\n"
             f"Source: specs/factory-internal/{target_file.name}\n"
             f"Destination: specs/inbox/{slug}.md\n"
             f"Severity was: {item['severity']}. "
             f"Intent enters spec pipeline for full NLSpec drafting."],
            cwd=workspace, capture_output=True, text=True,
        )
        if result.returncode == 0:
            console.print("  [dim]State committed to git.[/dim]")
        else:
            console.print(f"  [yellow]Warning:[/yellow] git commit failed: {result.stderr.strip()}")
        return

    # ── Display mode (no action flag) ──
    sev = item["severity"]
    status = item["status"]
    color = "red" if sev == "critical" else "yellow" if sev == "high" else "dim"
    age = _format_age(item["created"])

    console.print(f"\n[bold]{target_file.name}[/bold]")
    console.print(f"  severity:  [{color}]{sev}[/{color}]")
    console.print(f"  status:    {status}")
    console.print(f"  agent:     {item['source_agent']}")
    console.print(f"  type:      {item['source_type']}")
    console.print(f"  age:       {age}")
    console.print()
    console.print("[bold]Observation:[/bold]")
    for line in item["observation"].splitlines():
        console.print(f"  {line}")
    console.print()
    console.print("[bold]Available actions:[/bold]")
    console.print(f"  factory triage {target_file.name} --promote")
    console.print(f"  factory triage {target_file.name} --dismiss --reason \"...\"")


@main.command(name="cleanup-factory-internal")
@click.option("--dry-run", is_flag=True, default=False,
              help="Show what would be cleaned without deleting.")
def cleanup_factory_internal_cmd(dry_run: bool) -> None:
    """Remove factory-internal files when lifecycle criteria are met.

    Removes promoted files whose corresponding inbox spec has been archived,
    and dismissed files older than 30 days.
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    log_lines = cleanup_factory_internal(config.workspace, dry_run=dry_run)

    if not log_lines:
        console.print("[dim]Factory internal is clean — no files to remove.[/dim]")
        return

    prefix = "[dry-run] Would clean" if dry_run else "Cleaned"
    for line in log_lines:
        display = line.replace("Cleaned factory-internal:", f"{prefix}:")
        console.print(f"  {display}")


if __name__ == "__main__":
    main()
