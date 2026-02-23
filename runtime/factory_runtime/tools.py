"""Tool definitions and execution for factory agents.

Provides filesystem tools, shell tools, coordination tools,
and memory tools as described in Section 3 of the runtime spec.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from .access import AccessDenied, check_access
from .config import AgentConfig, FactoryConfig

# Maximum tool output size before truncation (1 MiB)
MAX_TOOL_OUTPUT = 1024 * 1024

# Commands blocked for read-only shell
WRITE_INDICATORS = [
    ">", ">>", "tee ", "mv ", "cp ", "rm ", "mkdir ", "chmod ", "chown ",
    "curl -o", "curl -O", "wget ", "pip install", "npm install",
]

# Commands explicitly allowed for read-only shell
READ_COMMANDS = [
    "cat", "head", "tail", "grep", "find", "ls", "wc", "diff",
    "git log", "git show", "git diff", "git status", "git branch",
    "pytest", "python -m pytest", "npm test", "cargo test", "go test",
]


def truncate_output(output: str) -> str:
    """Truncate tool output, keeping head and tail."""
    if len(output) <= MAX_TOOL_OUTPUT:
        return output

    lines = output.split("\n")
    # Keep first 200 and last 200 lines
    if len(lines) > 400:
        head = "\n".join(lines[:200])
        tail = "\n".join(lines[-200:])
        return (
            f"{head}\n\n"
            f"... [{len(lines) - 400} lines truncated] ...\n\n"
            f"{tail}"
        )
    return output[:MAX_TOOL_OUTPUT]


def get_tool_definitions(agent_config: AgentConfig) -> list[dict]:
    """Return tool definitions for the Anthropic API based on agent's capabilities."""
    tools = [
        {
            "name": "read_file",
            "description": "Read a file from the workspace. Path is relative to the workspace root.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path relative to workspace root",
                    }
                },
                "required": ["path"],
            },
        },
        {
            "name": "write_file",
            "description": "Write content to a file. Path is relative to the workspace root. Creates parent directories if needed.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path relative to workspace root",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write",
                    },
                },
                "required": ["path", "content"],
            },
        },
        {
            "name": "move_file",
            "description": "Move a file from one location to another. This IS a state transition in the task system.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "src": {
                        "type": "string",
                        "description": "Source path relative to workspace",
                    },
                    "dst": {
                        "type": "string",
                        "description": "Destination path relative to workspace",
                    },
                },
                "required": ["src", "dst"],
            },
        },
        {
            "name": "list_directory",
            "description": "List contents of a directory. Path is relative to workspace root.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path relative to workspace root",
                    }
                },
                "required": ["path"],
            },
        },
        {
            "name": "grep_files",
            "description": "Search for a text pattern in files within a directory.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory to search in, relative to workspace",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Text pattern or regex to search for",
                    },
                },
                "required": ["path", "pattern"],
            },
        },
        {
            "name": "request_research",
            "description": "Write a research request for the Researcher agent to pick up.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The research question",
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context for the researcher",
                    },
                },
                "required": ["question"],
            },
        },
        {
            "name": "remember",
            "description": "Append content to a memory file (daily log, MEMORY.md, or KNOWLEDGE.md).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Content to remember",
                    },
                    "target": {
                        "type": "string",
                        "description": "Target: 'daily' (default), 'private', or 'shared'",
                        "enum": ["daily", "private", "shared"],
                    },
                },
                "required": ["content"],
            },
        },
        {
            "name": "load_skill",
            "description": "Load the full content of an available skill by path.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "skill_path": {
                        "type": "string",
                        "description": "Skill path, e.g. 'researcher/research-approach'",
                    }
                },
                "required": ["skill_path"],
            },
        },
    ]

    # Add shell tool if agent has shell access
    if agent_config.shell_access != "none":
        tools.append(
            {
                "name": "run_command",
                "description": (
                    "Execute a shell command. "
                    + (
                        "You have full shell access."
                        if agent_config.shell_access == "full"
                        else "You have READ-ONLY shell access. Write operations will be blocked."
                    )
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Shell command to execute",
                        },
                        "cwd": {
                            "type": "string",
                            "description": "Working directory (default: workspace root)",
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds (default: 120)",
                        },
                    },
                    "required": ["command"],
                },
            }
        )

    return tools


def _is_read_only_safe(command: str) -> bool:
    """Check if a command is safe for read-only shell access."""
    for indicator in WRITE_INDICATORS:
        if indicator in command:
            return False
    return True


def execute_tool(
    tool_name: str,
    tool_input: dict,
    agent_config: AgentConfig,
    config: FactoryConfig,
) -> str:
    """Execute a tool call and return the result string.

    Enforces access control on all filesystem operations.
    """
    workspace = config.workspace

    try:
        if tool_name == "read_file":
            path = tool_input["path"]
            check_access(agent_config, workspace, "read", path)
            full_path = workspace / path
            if not full_path.exists():
                return f"Error: file not found: {path}"
            content = full_path.read_text()
            return truncate_output(content)

        elif tool_name == "write_file":
            path = tool_input["path"]
            content = tool_input["content"]
            check_access(agent_config, workspace, "write", path)
            full_path = workspace / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            return f"Written {len(content)} bytes to {path}"

        elif tool_name == "move_file":
            src = tool_input["src"]
            dst = tool_input["dst"]
            check_access(agent_config, workspace, "read", src)
            check_access(agent_config, workspace, "write", dst)
            src_full = workspace / src
            dst_full = workspace / dst
            if not src_full.exists():
                return f"Error: source not found: {src}"
            dst_full.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_full), str(dst_full))
            return f"Moved {src} → {dst}"

        elif tool_name == "list_directory":
            path = tool_input["path"]
            check_access(agent_config, workspace, "read", path)
            full_path = workspace / path
            if not full_path.exists():
                return f"Error: directory not found: {path}"
            if not full_path.is_dir():
                return f"Error: not a directory: {path}"
            entries = sorted(full_path.iterdir())
            lines = []
            for entry in entries:
                if entry.name.startswith("."):
                    continue
                suffix = "/" if entry.is_dir() else ""
                lines.append(f"{entry.name}{suffix}")
            return "\n".join(lines) if lines else "(empty directory)"

        elif tool_name == "grep_files":
            path = tool_input["path"]
            pattern = tool_input["pattern"]
            check_access(agent_config, workspace, "read", path)
            full_path = workspace / path
            if not full_path.exists():
                return f"Error: path not found: {path}"

            try:
                result = subprocess.run(
                    ["grep", "-r", "-n", "--include=*.md", "--include=*.yaml",
                     "--include=*.yml", "--include=*.py", "--include=*.toml",
                     "--include=*.json", "--include=*.txt",
                     pattern, str(full_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                output = result.stdout or "(no matches)"
                return truncate_output(output)
            except subprocess.TimeoutExpired:
                return "Error: search timed out after 30s"

        elif tool_name == "request_research":
            question = tool_input["question"]
            context = tool_input.get("context", "")
            # Write to tasks/research/
            check_access(agent_config, workspace, "write", "tasks/research/")
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"{agent_config.name}-{timestamp}.md"
            req_path = workspace / "tasks" / "research" / filename
            content = f"# Research Request\n\n**From:** {agent_config.name}\n**Date:** {datetime.now().isoformat()}\n\n## Question\n\n{question}\n"
            if context:
                content += f"\n## Context\n\n{context}\n"
            req_path.write_text(content)
            return f"Research request written to tasks/research/{filename}"

        elif tool_name == "remember":
            content = tool_input["content"]
            target = tool_input.get("target", "daily")
            today = datetime.now().strftime("%Y-%m-%d")
            now = datetime.now().strftime("%H:%M")

            if target == "daily":
                path = f"{agent_config.memory_daily}{today}.md"
                check_access(agent_config, workspace, "write", path)
                full_path = workspace / path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                entry = f"\n## {now}\n\n{content}\n"
                with open(full_path, "a") as f:
                    f.write(entry)
                return f"Appended to daily log: {path}"

            elif target == "private":
                path = agent_config.memory_private
                check_access(agent_config, workspace, "write", path)
                full_path = workspace / path
                entry = f"\n## {today}\n\n{content}\n"
                with open(full_path, "a") as f:
                    f.write(entry)
                return f"Appended to private memory: {path}"

            elif target == "shared":
                path = "memory/shared/KNOWLEDGE.md"
                check_access(agent_config, workspace, "write", path)
                full_path = workspace / path
                entry = f"\n## {today} ({agent_config.name})\n\n{content}\n"
                with open(full_path, "a") as f:
                    f.write(entry)
                return f"Appended to shared knowledge: {path}"

            return f"Error: unknown memory target: {target}"

        elif tool_name == "load_skill":
            skill_path = tool_input["skill_path"]
            from .context import load_skill_content
            content = load_skill_content(workspace, skill_path)
            if content is None:
                return f"Error: skill not found: {skill_path}"
            return content

        elif tool_name == "run_command":
            if agent_config.shell_access == "none":
                return "Error: you do not have shell access."

            command = tool_input["command"]
            cwd = tool_input.get("cwd", str(workspace))
            timeout = tool_input.get("timeout", 120)

            # Enforce read-only shell
            if agent_config.shell_access == "read_only":
                if not _is_read_only_safe(command):
                    return (
                        f"Error: command blocked — you have read-only shell access. "
                        f"Write operations are not permitted."
                    )

            # Resolve cwd relative to workspace
            if not os.path.isabs(cwd):
                cwd = str(workspace / cwd)

            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=cwd,
                )
                output = ""
                if result.stdout:
                    output += result.stdout
                if result.stderr:
                    output += f"\n[stderr]\n{result.stderr}"
                if result.returncode != 0:
                    output += f"\n[exit code: {result.returncode}]"
                return truncate_output(output) if output else "(no output)"
            except subprocess.TimeoutExpired:
                return f"Error: command timed out after {timeout}s"

        else:
            return f"Error: unknown tool: {tool_name}"

    except AccessDenied as e:
        return str(e)
    except Exception as e:
        return f"Error executing {tool_name}: {type(e).__name__}: {e}"
