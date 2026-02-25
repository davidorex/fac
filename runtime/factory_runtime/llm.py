"""Dispatcher for factory agent execution.

Owns context assembly, ACL prompt construction, governance pre/post
checks, and backend selection. Delegates actual CLI invocation to the
appropriate backend based on agent_config.provider.

Provider routing:
  provider: anthropic (default) → backends/anthropic.py (Claude Code CLI)
  provider: kimi                → backends/kimi.py (kimi-cli)
  provider: <unknown>           → ValueError naming available backends

Governance model:
  Pre-execution: mandate text injected into system prompt (backend-agnostic).
    For anthropic, mandates also appear via Claude Code's UserPromptSubmit
    hook — intentionally redundant to ensure uniform coverage.
  Post-execution: pass-through seam; logs completion, runs no checks yet.
    Slot future governance checks here without changing the dispatcher.
  Per-tool-call: anthropic only (PreToolUse/PostToolUse via Claude Code hooks).
    Not replicable at the dispatcher level for other backends — documented
    gap in backends/capabilities.md.
"""

from __future__ import annotations

import json
from pathlib import Path

from .config import AgentConfig, FactoryConfig
from .context import assemble_context
from .run_log import RunLogger


def _build_user_prompt(messages: list[dict]) -> str:
    """Flatten assembled messages into a single user prompt string."""
    user_prompt = ""
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            user_prompt += content + "\n"
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and "content" in part:
                    user_prompt += str(part["content"]) + "\n"
    return user_prompt


def _build_acl_prompt(agent_config: AgentConfig, config: FactoryConfig) -> str:
    """Build access control instructions appended to the system prompt.

    ACL enforcement is a runtime/dispatcher concern — not a backend concern.
    The same ACL text is injected regardless of which backend executes.
    """
    workspace = config.workspace
    lines = [
        "## CRITICAL: Access Control Rules",
        "",
        f"Your workspace root is: {workspace}",
        "You MUST obey these access control rules. Violations are logged and reported.",
        "",
        "### Files you CAN read:",
    ]
    for rule in agent_config.can_read:
        lines.append(f"- {rule}")

    lines.extend([
        "",
        "### Files you CAN write:",
    ])
    for rule in agent_config.can_write:
        lines.append(f"- {rule}")

    if agent_config.cannot_access:
        lines.extend([
            "",
            "### Files you CANNOT access (read or write):",
        ])
        for rule in agent_config.cannot_access:
            lines.append(f"- {rule} — ACCESS DENIED")

    lines.extend([
        "",
        "### Universal rules:",
        "- universe/ is READ-ONLY for all agents. Never write to universe/.",
        "- agents.yaml is READ-ONLY. Never modify agents.yaml.",
        "- Always work with paths relative to the workspace root.",
        "",
        "### State transitions:",
        "Moving files between directories signals state changes.",
        "After completing work, move files to the appropriate next-stage directory.",
        "Commit to git after every meaningful state change.",
    ])

    return "\n".join(lines)


def _load_mandates(config: FactoryConfig) -> list[dict]:
    """Load mandate rules from mandate files.

    Checks ~/.claude/mandates.jsonl (global) and
    {workspace}/.claude/mandates.jsonl (project-local), in that order.
    Each line is a JSON object with at minimum 'title' and 'rule' fields.
    """
    mandates: list[dict] = []
    candidate_paths = [
        Path.home() / ".claude" / "mandates.jsonl",
        config.workspace / ".claude" / "mandates.jsonl",
    ]
    for path in candidate_paths:
        if path.exists():
            for line in path.read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    mandates.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return mandates


def _format_mandates(mandates: list[dict]) -> str:
    """Format mandate list into system prompt injection text."""
    lines = [
        "## Behavioral Mandates",
        "",
        "The following mandates govern your behavior in this session:",
        "",
    ]
    for m in mandates:
        title = m.get("title", "")
        rule = m.get("rule", "")
        if title and rule:
            lines.append(f"- **{title}**: {rule}")
        elif rule:
            lines.append(f"- {rule}")
    return "\n".join(lines)


def run_pre_governance(
    config: FactoryConfig,
    agent_config: AgentConfig,
    system_prompt: str,
    user_prompt: str,
    run_logger: RunLogger | None = None,
) -> tuple[str, str]:
    """Run pre-execution governance checks.

    Injects mandate text into the system prompt. For the anthropic backend,
    Claude Code's UserPromptSubmit hook also injects mandates — the
    redundancy is intentional (belt-and-suspenders for governance coverage).
    For non-Claude backends, this is the sole mandate injection mechanism.

    Returns (system_prompt, user_prompt) with any governance modifications.
    """
    mandates = _load_mandates(config)

    if mandates:
        mandate_text = _format_mandates(mandates)
        system_prompt = system_prompt + "\n\n" + mandate_text

    if run_logger:
        run_logger.log_event("governance_pre", {
            "mandate_count": len(mandates),
            "provider": agent_config.provider,
            "mandates_injected": bool(mandates),
        })

    return system_prompt, user_prompt


def run_post_governance(
    config: FactoryConfig,
    agent_config: AgentConfig,
    result: str,
    run_logger: RunLogger | None = None,
) -> str:
    """Run post-execution governance checks.

    Currently a pass-through seam: logs completion, returns result unchanged.
    Future governance logic (output validation, policy checks) slots here
    without requiring changes to the dispatcher or backends.
    """
    if run_logger:
        run_logger.log_event("governance_post", {
            "provider": agent_config.provider,
            "result_length": len(result),
            "is_no_reply": result.strip().upper() == "NO_REPLY",
        })

    return result


def validate_providers(config: FactoryConfig) -> list[str]:
    """Validate that all declared providers have discoverable CLI binaries.

    Returns a list of warning strings for missing binaries. Missing binaries
    are warnings only — agents using working backends are unaffected.

    Intended for startup validation: call this after config load and print
    any returned warnings before dispatching to agents.
    """
    from .backends import get_backend

    warnings: list[str] = []
    checked: set[str] = set()

    for agent_name, agent_config in config.agents.items():
        provider = agent_config.provider
        if provider in checked:
            continue
        checked.add(provider)

        try:
            backend = get_backend(provider)
            backend._find_cli()
        except FileNotFoundError as e:
            warnings.append(
                f"Warning: provider '{provider}' binary not found ({e}). "
                f"Agents using this provider will fail at dispatch time."
            )
        except ValueError:
            # Unknown provider — surfaces as a clear error at dispatch time
            pass

    return warnings


def run_agent(
    config: FactoryConfig,
    agent_config: AgentConfig,
    task_content: str | None = None,
    message: str | None = None,
    is_heartbeat: bool = False,
    run_logger: RunLogger | None = None,
) -> str:
    """Dispatch a single agent invocation to the appropriate backend.

    Assembles context (system prompt + user prompt), applies ACL, runs
    pre-execution governance, dispatches to the backend selected by
    agent_config.provider, then runs post-execution governance.

    Returns the agent's final text response.

    This is the single public entry point for all agent execution —
    callers do not need to know which backend is active.
    """
    from .backends import get_backend

    # Select backend — raises ValueError with clear message for unknown providers
    backend = get_backend(agent_config.provider)

    # Context assembly is a dispatcher concern, not a backend concern
    system_prompt, messages, context_bar = assemble_context(
        config, agent_config, task_content, message, is_heartbeat,
    )

    user_prompt = _build_user_prompt(messages)

    # ACL injection — same text regardless of backend
    acl_prompt = _build_acl_prompt(agent_config, config)
    system_prompt = system_prompt + "\n\n" + acl_prompt

    # Log assembled context before governance modifies system_prompt
    if run_logger:
        run_logger.log_context(system_prompt, messages)
        run_logger.log_event("context_bar", context_bar)
        run_logger.log_event("provider", agent_config.provider)

    # Pre-execution governance — mandate injection
    system_prompt, user_prompt = run_pre_governance(
        config, agent_config, system_prompt, user_prompt, run_logger,
    )

    # Dispatch to backend
    result = backend.run_agent(
        config=config,
        agent_config=agent_config,
        task_content=task_content,
        message=message,
        is_heartbeat=is_heartbeat,
        run_logger=run_logger,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    # Post-execution governance — pass-through seam
    result = run_post_governance(config, agent_config, result, run_logger)

    return result
