"""kimi-cli backend for factory agent execution.

Invokes agents via the `kimi-cli` binary (Moonshot AI, v1.12.0+).
Operates in text-only mode (--output-format text): the full response
is captured after the run completes. No live streaming.

Key differences from the Anthropic backend:
- System prompt delivered via a temporary agent YAML file, not --system-prompt
- User prompt passed as a -p flag argument, not via stdin
- Tool authorization via agent file exclude_tools/tools, not --allowedTools
- No hook system: per-tool-call governance is not available
- Model names passed through directly (no aliasing)

Binary name: kimi-cli (not kimi, which is aliased to kimi-amos in
interactive shells). kimi-cli is unambiguous in all contexts.
"""

from __future__ import annotations

import os
import subprocess
import shutil
import time
import uuid
from pathlib import Path

import yaml

from ..config import AgentConfig, FactoryConfig
from ..run_log import RunLogger
from .common import DIM, RED, RESET


def _find_cli() -> str:
    """Find the kimi-cli binary.

    Uses kimi-cli (not kimi) to avoid the shell alias kimi→kimi-amos.
    The alias is active in interactive shells but not in subprocess
    invocation — using the unambiguous binary name avoids this entirely.
    """
    kimi = shutil.which("kimi-cli")
    if kimi:
        return kimi
    for path in [
        os.path.expanduser("~/.local/bin/kimi-cli"),
        "/usr/local/bin/kimi-cli",
    ]:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    raise FileNotFoundError(
        "kimi-cli not found. Install from: https://github.com/MoonshotAI/kimi-cli\n"
        "Expected at ~/.local/bin/kimi-cli or /usr/local/bin/kimi-cli"
    )


def _build_exclude_tools(agent_config: AgentConfig) -> list[str]:
    """Build kimi-cli exclude_tools list from agent permissions.

    Translates factory agent permission flags into kimi_cli tool class
    references (kimi_cli.tools.module:ClassName format).
    """
    exclude: list[str] = []
    if agent_config.shell_access == "none":
        exclude.append("kimi_cli.tools.shell:Shell")
    return exclude


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
    """Run a single agent invocation via kimi-cli.

    Writes a temporary agent YAML file (required for system prompt
    delivery — kimi-cli does not support --system-prompt inline).
    Cleans up temp files in a finally block regardless of outcome.

    Text-only output mode: operator has no live visibility into
    activity during long runs. This is an accepted trade-off for the
    initial implementation; streaming is a follow-up.

    Returns the agent's final text response.
    """
    kimi_bin = _find_cli()

    run_id = uuid.uuid4().hex[:8]
    prompt_path = Path(f"/tmp/factory-prompt-{run_id}.md")
    agent_file_path = Path(f"/tmp/factory-agent-{run_id}.yaml")

    try:
        # Write the system prompt to a temp file — kimi-cli reads it
        # via system_prompt_path in the agent YAML
        prompt_path.write_text(system_prompt or "")

        # Build the agent YAML
        exclude_tools = _build_exclude_tools(agent_config)
        agent_data: dict = {
            "version": 1,
            "agent": {
                "extend": "default",
                "system_prompt_path": str(prompt_path),
            },
        }
        if exclude_tools:
            agent_data["agent"]["exclude_tools"] = exclude_tools

        agent_file_path.write_text(yaml.dump(agent_data, default_flow_style=False))

        # Build the kimi-cli invocation
        # --print enables non-interactive mode (implicitly --yolo for
        # auto-approval of tool calls). User prompt via -p flag, not stdin.
        cmd = [
            kimi_bin,
            "--print",
            "--output-format", "text",
            "--agent-file", str(agent_file_path),
        ]

        if agent_config.model:
            cmd.extend(["--model", agent_config.model])

        # User prompt as -p flag argument (not stdin — kimi-cli differs
        # from Claude Code in this respect)
        cmd.extend(["-p", user_prompt or ""])

        if run_logger:
            run_logger.log_event("kimi_cmd", " ".join(cmd[:8]) + "...")

        print(f"\n  {DIM}{'─' * 50}{RESET}")
        print(f"  {DIM}Running kimi-cli (text mode — no live streaming){RESET}")
        print(f"  {DIM}Agent file: {agent_file_path}{RESET}\n")

        start_time = time.time()

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(config.workspace),
            timeout=1800,
        )

        elapsed = time.time() - start_time

        final_result = proc.stdout.strip()

        print(f"  {DIM}{'─' * 50}{RESET}")
        print(f"  {DIM}Done in {elapsed:.1f}s{RESET}\n")

        if proc.stderr:
            if run_logger:
                run_logger.log_event("stderr", proc.stderr[:2000])

        if proc.returncode != 0 and not final_result:
            final_result = f"Error (exit {proc.returncode}): {proc.stderr[:500]}"

        if run_logger:
            run_logger.log_outcome(final_result)

        return final_result

    except subprocess.TimeoutExpired:
        error_msg = "Agent run timed out after 1800 seconds"
        print(f"\n  {RED}⚠  {error_msg}{RESET}\n")
        if run_logger:
            run_logger.log_outcome(f"ERROR: {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Error running kimi-cli: {e}"
        print(f"\n  {RED}⚠  {error_msg}{RESET}\n")
        if run_logger:
            run_logger.log_outcome(f"ERROR: {error_msg}")
        raise
    finally:
        # Always clean up temp files — happy path and error paths both
        for path in [prompt_path, agent_file_path]:
            try:
                if path.exists():
                    path.unlink()
            except Exception:
                pass
