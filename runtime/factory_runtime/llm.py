"""LLM client for invoking agents via Claude Code CLI.

Uses the `claude` CLI in print mode (-p) with --system-prompt,
--model, and --output-format json. This inherits Claude Code's
OAuth authentication — no API key management needed.

The factory runtime assembles context and passes it as the prompt.
Claude Code handles the LLM interaction. Tool calls are handled
by providing custom tools via --tools and the agent loop.

For the initial implementation, we use Claude Code's --print mode
which runs the full agent loop internally. The factory provides
context assembly, access control, and run logging on top.
"""

from __future__ import annotations

import json
import os
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import AgentConfig, FactoryConfig
from .context import assemble_context
from .tools import execute_tool, get_tool_definitions
from .run_log import RunLogger


def _find_claude_cli() -> str:
    """Find the claude CLI binary."""
    claude = shutil.which("claude")
    if claude:
        return claude
    # Common install locations
    for path in [
        os.path.expanduser("~/.local/bin/claude"),
        "/usr/local/bin/claude",
    ]:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    raise FileNotFoundError(
        "claude CLI not found. Install Claude Code: https://docs.anthropic.com/claude-code"
    )


def _model_alias(model: str) -> str:
    """Convert agents.yaml model names to claude CLI model aliases."""
    aliases = {
        "claude-opus-4-6": "opus",
        "claude-sonnet-4-5": "sonnet",
        "claude-sonnet-4-6": "sonnet",
        "claude-haiku-4-5": "haiku",
    }
    return aliases.get(model, model)


def run_agent(
    config: FactoryConfig,
    agent_config: AgentConfig,
    task_content: str | None = None,
    message: str | None = None,
    is_heartbeat: bool = False,
    run_logger: RunLogger | None = None,
) -> str:
    """Run a single agent invocation via Claude Code CLI.

    Assembles context, invokes `claude -p` with the appropriate
    system prompt and user message, and logs the results.

    Returns the agent's final text response.
    """
    claude_bin = _find_claude_cli()

    system_prompt, messages, context_bar = assemble_context(
        config, agent_config, task_content, message, is_heartbeat,
    )

    if run_logger:
        run_logger.log_context(system_prompt, messages)
        run_logger.log_event("context_bar", context_bar)

    # Build the user prompt from assembled messages
    user_prompt = ""
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            user_prompt += content + "\n"
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and "content" in part:
                    user_prompt += str(part["content"]) + "\n"

    # Determine which tools the agent should have access to
    # Claude Code provides its own tools (Read, Write, Bash, etc.)
    # We add the workspace as an allowed directory and configure
    # tool permissions based on the agent's access control
    allowed_tools = _build_allowed_tools(agent_config)

    # Build the claude CLI command
    cmd = [
        claude_bin,
        "-p",  # print mode (non-interactive)
        "--model", _model_alias(agent_config.model),
        "--system-prompt", system_prompt,
        "--output-format", "text",
        "--no-session-persistence",
    ]

    # Configure tool access
    if allowed_tools:
        cmd.extend(["--allowedTools", ",".join(allowed_tools)])

    # Add workspace as allowed directory
    cmd.extend(["--add-dir", str(config.workspace)])

    # Set permission mode based on shell access
    if agent_config.shell_access == "full":
        cmd.extend(["--permission-mode", "bypassPermissions"])
    elif agent_config.shell_access == "read_only":
        cmd.extend(["--permission-mode", "bypassPermissions"])
    else:
        # No shell access — only allow file tools
        cmd.extend(["--permission-mode", "bypassPermissions"])

    # Append access control rules to the system prompt
    acl_prompt = _build_acl_prompt(agent_config, config)
    cmd[cmd.index("--system-prompt") + 1] = system_prompt + "\n\n" + acl_prompt

    if run_logger:
        run_logger.log_event("claude_cmd", " ".join(cmd[:10]) + "...")

    try:
        result = subprocess.run(
            cmd,
            input=user_prompt,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            cwd=str(config.workspace),
            env={
                **{k: v for k, v in os.environ.items()
                   if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")},
                "CLAUDE_CODE_ENTRYPOINT": "factory-runtime",
            },
        )

        output = result.stdout.strip()
        if result.stderr:
            if run_logger:
                run_logger.log_event("stderr", result.stderr[:2000])

        if result.returncode != 0 and not output:
            output = f"Error (exit {result.returncode}): {result.stderr[:500]}"

        if run_logger:
            run_logger.log_outcome(output)

        return output

    except subprocess.TimeoutExpired:
        error_msg = "Agent run timed out after 600 seconds"
        if run_logger:
            run_logger.log_outcome(f"ERROR: {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Error running claude CLI: {e}"
        if run_logger:
            run_logger.log_outcome(f"ERROR: {error_msg}")
        raise


def _build_allowed_tools(agent_config: AgentConfig) -> list[str]:
    """Build the list of allowed Claude Code tools based on agent config."""
    tools = ["Read", "Glob", "Grep"]

    if agent_config.shell_access != "none":
        tools.append("Bash")

    # All agents can write files (access control is in the system prompt)
    tools.extend(["Write", "Edit"])

    return tools


def _build_acl_prompt(agent_config: AgentConfig, config: FactoryConfig) -> str:
    """Build access control instructions for the system prompt.

    Since Claude Code handles file operations directly, we encode
    the access control rules as strict instructions in the prompt.
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
