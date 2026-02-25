"""Shared utilities for factory agent backends.

ANSI colors, path formatting, and tool-use display logic used by
multiple backend implementations. Extracted from llm.py to avoid
duplication across backends.
"""

from __future__ import annotations


# ANSI colors for terminal output
DIM = "\033[2m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RED = "\033[31m"
RESET = "\033[0m"


def _short_path(path: str) -> str:
    """Shorten absolute paths to be relative to factory workspace."""
    for prefix in ("/Users/david/Projects/fac/factory/", "/Users/david/Projects/fac/"):
        if path.startswith(prefix):
            return path[len(prefix):]
    return path


def _format_tool_use(tool: str, tool_input: dict) -> str:
    """Format a tool_use block into a concise log line."""
    if tool == "Read":
        path = tool_input.get("file_path", "?")
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
