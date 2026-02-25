"""Anthropic (Claude Code CLI) backend for factory agent execution.

Invokes agents via the `claude` CLI in print mode with stream-json output.
Live-streams events to the terminal so the operator can see activity in
real time. Returns the agent's final text response.

This backend retains full hook-based governance (UserPromptSubmit,
PreToolUse, PostToolUse) because Claude Code executes the hooks
natively. Per-tool-call governance is a Claude-only capability.
"""

from __future__ import annotations

import json
import os
import subprocess
import shutil
import sys
import threading
import time

from ..config import AgentConfig, FactoryConfig
from ..run_log import RunLogger
from .common import (
    CYAN, DIM, GREEN, RED, RESET, YELLOW,
    _format_tool_use,
)


def _find_cli() -> str:
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
    Claude Code uses an event-type schema distinct from kimi's
    conversation-turn schema.
    """
    etype = event.get("type", "")

    # Assistant text output
    if etype == "assistant":
        message = event.get("message", {})
        content = event.get("message", {}).get("content", [])
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


def _build_allowed_tools(agent_config: AgentConfig) -> list[str]:
    """Build the list of allowed Claude Code tools based on agent config."""
    tools = ["Read", "Glob", "Grep"]

    if agent_config.shell_access != "none":
        tools.append("Bash")

    # All agents can write files (access control is enforced via system prompt)
    tools.extend(["Write", "Edit"])

    return tools


def run_agent(
    config: FactoryConfig,
    agent_config: AgentConfig,
    task_content: str | None = None,
    message: str | None = None,
    is_heartbeat: bool = False,
    run_logger: RunLogger | None = None,
    system_prompt: str | None = None,
    user_prompt: str | None = None,
) -> str:
    """Run a single agent invocation via Claude Code CLI.

    Streams events to the terminal in real time and collects the
    final result for logging. The dispatcher has already assembled
    system_prompt and user_prompt — this backend focuses solely on
    CLI invocation and output capture.

    Returns the agent's final text response.
    """
    claude_bin = _find_cli()

    allowed_tools = _build_allowed_tools(agent_config)

    # Build the claude CLI command — stream-json for live output
    cmd = [
        claude_bin,
        "-p",
        "--model", _model_alias(agent_config.model),
        "--system-prompt", system_prompt or "",
        "--output-format", "stream-json",
        "--verbose",
        "--no-session-persistence",
    ]

    if allowed_tools:
        cmd.extend(["--allowedTools", ",".join(allowed_tools)])

    cmd.extend(["--add-dir", str(config.workspace)])

    # Permission mode — all agents use bypassPermissions
    cmd.extend(["--permission-mode", "bypassPermissions"])

    if run_logger:
        run_logger.log_event("anthropic_cmd", " ".join(cmd[:10]) + "...")

    print(f"\n  {DIM}{'─' * 50}{RESET}")
    print(f"  {DIM}Streaming agent activity...{RESET}\n")

    start_time = time.time()
    final_result = ""
    event_count = 0
    proc: subprocess.Popen | None = None

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

        # Send user prompt via stdin and close
        if proc.stdin:
            proc.stdin.write(user_prompt or "")
            proc.stdin.close()

        # Read stderr in a background thread so it doesn't block stdout
        stderr_lines: list[str] = []

        def _read_stderr() -> None:
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
                    print(f"  {DIM}{line}{RESET}")
                    continue

                event_count += 1

                if run_logger:
                    run_logger.log_event(
                        f"stream_{event_count}",
                        json.dumps(event)[:2000],
                    )

                # Capture the final result from the result event
                if event.get("type") == "result":
                    result = event.get("result", "")
                    if isinstance(result, str):
                        final_result = result.strip()
                    elif isinstance(result, list):
                        texts = []
                        for block in result:
                            if isinstance(block, dict) and block.get("type") == "text":
                                texts.append(block.get("text", ""))
                        final_result = "\n".join(texts).strip()

                formatted = _format_event(event)
                if formatted:
                    elapsed = time.time() - start_time
                    timestamp = f"{DIM}[{elapsed:6.1f}s]{RESET}"
                    print(f"  {timestamp} {formatted}")
                    sys.stdout.flush()

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
