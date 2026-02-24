"""LLM client for invoking agents via Claude Code CLI.

Uses the `claude` CLI in print mode (-p) with --system-prompt,
--model, and --output-format stream-json. Streams events to the
terminal in real time so the operator can see what's happening.

The factory runtime assembles context and passes it as the prompt.
Claude Code handles the LLM interaction and tool execution internally.
"""

from __future__ import annotations

import json
import os
import select
import subprocess
import shutil
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import AgentConfig, FactoryConfig
from .context import assemble_context
from .tools import execute_tool, get_tool_definitions
from .run_log import RunLogger


# ANSI colors for terminal output
DIM = "\033[2m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RED = "\033[31m"
RESET = "\033[0m"


def _find_claude_cli() -> str:
    """Find the claude CLI binary."""
    claude = shutil.which("claude")
    if claude:
        return claude
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


def _format_event(event: dict) -> str | None:
    """Format a stream-json event into a human-readable log line.

    Returns None for events that should be suppressed (noise).
    """
    etype = event.get("type", "")

    # Assistant text output
    if etype == "assistant":
        message = event.get("message", {})
        # Extract text from content blocks
        content = message.get("content", [])
        texts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    text = block.get("text", "").strip()
                    if text:
                        texts.append(text)
                elif block.get("type") == "tool_use":
                    tool = block.get("name", "?")
                    tool_input = block.get("input", {})
                    return _format_tool_use(tool, tool_input)
        if texts:
            # Truncate long text output for the live view
            combined = " ".join(texts)
            if len(combined) > 200:
                combined = combined[:200] + "..."
            return f"{CYAN}💬 {combined}{RESET}"

    # Tool result
    elif etype == "result":
        result_text = event.get("result", "")
        if isinstance(result_text, str):
            result_text = result_text.strip()
            if result_text.upper() == "NO_REPLY":
                return f"{DIM}⏸  NO_REPLY — nothing to do{RESET}"
            if len(result_text) > 200:
                result_text = result_text[:200] + "..."
            return f"{GREEN}✓  Result: {result_text}{RESET}"

    # System messages
    elif etype == "system":
        msg = event.get("message", "")
        if isinstance(msg, str) and msg.strip():
            return f"{DIM}⚙  {msg.strip()}{RESET}"

    return None


def _format_tool_use(tool: str, tool_input: dict) -> str:
    """Format a tool_use block into a concise log line."""
    if tool == "Read":
        path = tool_input.get("file_path", "?")
        # Show just the relative path
        path = _short_path(path)
        return f"{YELLOW}📖 Read {path}{RESET}"

    elif tool == "Write":
        path = tool_input.get("file_path", "?")
        path = _short_path(path)
        return f"{YELLOW}✏️  Write {path}{RESET}"

    elif tool == "Edit":
        path = tool_input.get("file_path", "?")
        path = _short_path(path)
        old = tool_input.get("old_string", "")[:40]
        return f"{YELLOW}✏️  Edit {path} ({old}...){RESET}"

    elif tool == "Bash":
        cmd = tool_input.get("command", "?")
        if len(cmd) > 80:
            cmd = cmd[:80] + "..."
        return f"{YELLOW}🖥  Bash: {cmd}{RESET}"

    elif tool == "Glob":
        pattern = tool_input.get("pattern", "?")
        return f"{YELLOW}🔍 Glob {pattern}{RESET}"

    elif tool == "Grep":
        pattern = tool_input.get("pattern", "?")
        return f"{YELLOW}🔍 Grep '{pattern}'{RESET}"

    elif tool in ("WebSearch", "WebFetch"):
        query = tool_input.get("query", tool_input.get("url", "?"))
        return f"{YELLOW}🌐 {tool}: {query}{RESET}"

    elif tool == "TodoWrite":
        return f"{YELLOW}📋 Updating task list{RESET}"

    else:
        return f"{YELLOW}🔧 {tool}{RESET}"


def _short_path(path: str) -> str:
    """Shorten absolute paths to be relative to factory workspace."""
    # Try to strip common prefixes
    for prefix in ("/Users/david/Projects/fac/factory/", "/Users/david/Projects/fac/"):
        if path.startswith(prefix):
            return path[len(prefix):]
    return path


def run_agent(
    config: FactoryConfig,
    agent_config: AgentConfig,
    task_content: str | None = None,
    message: str | None = None,
    is_heartbeat: bool = False,
    run_logger: RunLogger | None = None,
) -> str:
    """Run a single agent invocation via Claude Code CLI.

    Streams events to the terminal in real time and collects the
    final result for logging.

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

    allowed_tools = _build_allowed_tools(agent_config)

    # Build the claude CLI command — stream-json for live output
    cmd = [
        claude_bin,
        "-p",
        "--model", _model_alias(agent_config.model),
        "--system-prompt", system_prompt,
        "--output-format", "stream-json",
        "--verbose",
        "--no-session-persistence",
    ]

    if allowed_tools:
        cmd.extend(["--allowedTools", ",".join(allowed_tools)])

    cmd.extend(["--add-dir", str(config.workspace)])

    # Permission mode (all agents get bypass for now)
    if agent_config.shell_access == "full":
        cmd.extend(["--permission-mode", "bypassPermissions"])
    elif agent_config.shell_access == "read_only":
        cmd.extend(["--permission-mode", "bypassPermissions"])
    else:
        cmd.extend(["--permission-mode", "bypassPermissions"])

    # Append ACL to system prompt
    acl_prompt = _build_acl_prompt(agent_config, config)
    cmd[cmd.index("--system-prompt") + 1] = system_prompt + "\n\n" + acl_prompt

    if run_logger:
        run_logger.log_event("claude_cmd", " ".join(cmd[:10]) + "...")

    # Print the streaming header
    print(f"\n  {DIM}{'─' * 50}{RESET}")
    print(f"  {DIM}Streaming agent activity...{RESET}\n")

    start_time = time.time()
    final_result = ""
    event_count = 0

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(config.workspace),
            env={
                **{k: v for k, v in os.environ.items()
                   if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")},
                "CLAUDE_CODE_ENTRYPOINT": "factory-runtime",
            },
        )

        # Send user prompt and close stdin
        if proc.stdin:
            proc.stdin.write(user_prompt)
            proc.stdin.close()

        # Read stderr in a background thread so it doesn't block
        stderr_lines = []
        def _read_stderr():
            if proc.stderr:
                for line in proc.stderr:
                    stderr_lines.append(line)
        stderr_thread = threading.Thread(target=_read_stderr, daemon=True)
        stderr_thread.start()

        # Stream stdout line by line — each line is a JSON event
        if proc.stdout:
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    # Not JSON — probably raw text, print it
                    print(f"  {DIM}{line}{RESET}")
                    continue

                event_count += 1

                # Log raw event
                if run_logger:
                    run_logger.log_event(
                        f"stream_{event_count}",
                        json.dumps(event)[:2000]
                    )

                # Capture the final result
                if event.get("type") == "result":
                    result = event.get("result", "")
                    if isinstance(result, str):
                        final_result = result.strip()
                    elif isinstance(result, list):
                        # Sometimes result is a list of content blocks
                        texts = []
                        for block in result:
                            if isinstance(block, dict) and block.get("type") == "text":
                                texts.append(block.get("text", ""))
                        final_result = "\n".join(texts).strip()

                # Format and print
                formatted = _format_event(event)
                if formatted:
                    elapsed = time.time() - start_time
                    timestamp = f"{DIM}[{elapsed:6.1f}s]{RESET}"
                    print(f"  {timestamp} {formatted}")
                    sys.stdout.flush()

        # Wait for process to finish
        proc.wait(timeout=1800)
        stderr_thread.join(timeout=5)

        elapsed = time.time() - start_time
        print(f"\n  {DIM}{'─' * 50}{RESET}")
        print(f"  {DIM}Done in {elapsed:.1f}s ({event_count} events){RESET}\n")

        if stderr_lines:
            stderr_text = "".join(stderr_lines)
            if run_logger:
                run_logger.log_event("stderr", stderr_text[:2000])

        if proc.returncode != 0 and not final_result:
            stderr_text = "".join(stderr_lines)
            final_result = f"Error (exit {proc.returncode}): {stderr_text[:500]}"

        if run_logger:
            run_logger.log_outcome(final_result)

        return final_result

    except subprocess.TimeoutExpired:
        if proc:
            proc.kill()
        error_msg = "Agent run timed out after 1800 seconds"
        print(f"\n  {RED}⚠  {error_msg}{RESET}\n")
        if run_logger:
            run_logger.log_outcome(f"ERROR: {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Error running claude CLI: {e}"
        print(f"\n  {RED}⚠  {error_msg}{RESET}\n")
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
    """Build access control instructions for the system prompt."""
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
