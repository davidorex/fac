"""Context assembly for agent invocations.

Builds the system prompt, loads skills, memory, and task context
according to Section 2 of the factory runtime spec.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

import yaml

from .config import AgentConfig, FactoryConfig


# Model context window sizes (tokens). Conservative estimates.
MODEL_CONTEXT_WINDOWS = {
    "claude-opus-4-6": 200_000,
    "claude-sonnet-4-5": 200_000,
    "claude-sonnet-4-6": 200_000,
    "claude-haiku-4-5": 200_000,
}

# Rough tokens-per-character ratio for estimation
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Rough token estimate from character count."""
    return len(text) // CHARS_PER_TOKEN


def context_color(pct: float) -> tuple[str, str]:
    """Return (color_name, hex_color) for a context usage percentage."""
    if pct <= 30:
        return ("GREEN", "#22c55e")
    if pct <= 50:
        return ("YELLOW", "#eab308")
    if pct <= 70:
        return ("ORANGE", "#f97316")
    if pct <= 90:
        return ("RED", "#ef4444")
    return ("DARK RED", "#991b1b")


def build_context_bar(pct: float) -> str:
    """Build the visual context budget bar."""
    filled = int(pct / 5)  # 20 characters total
    empty = 20 - filled
    color_name, _ = context_color(pct)
    bar = "█" * filled + "░" * empty
    return f"Context: {bar} {pct:.0f}% [{color_name}]"


def load_skill_content(workspace: Path, skill_path: str) -> str | None:
    """Load the full content of a skill file."""
    # skill_path is like "shared/filesystem-conventions"
    full_path = workspace / "skills" / skill_path / "SKILL.md"
    if full_path.exists():
        return full_path.read_text()
    return None


def load_skill_summary(workspace: Path, skill_path: str) -> str | None:
    """Load just the name and description from a skill's YAML frontmatter."""
    content = load_skill_content(workspace, skill_path)
    if content is None:
        return None

    # Parse YAML frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                meta = yaml.safe_load(parts[1])
                name = meta.get("name", skill_path.split("/")[-1])
                desc = meta.get("description", "")
                return f"- {name}: {desc}"
            except yaml.YAMLError:
                pass
    return f"- {skill_path}"


def assemble_system_prompt(
    config: FactoryConfig,
    agent_config: AgentConfig,
    timestamp: datetime | None = None,
) -> str:
    """Build the system prompt for an agent invocation.

    Includes agent identity, always-loaded skills, and the skill menu.
    """
    if timestamp is None:
        timestamp = datetime.now()

    workspace = config.workspace
    parts: list[str] = []

    # Agent identity
    parts.append(
        f"You are {agent_config.name}. {agent_config.role}\n"
        f"Current time: {timestamp.isoformat()}\n"
        f"Workspace: {workspace}\n"
    )

    # Access control summary
    parts.append("## Your Access Control\n")
    parts.append(f"Can read: {', '.join(agent_config.can_read)}")
    parts.append(f"Can write: {', '.join(agent_config.can_write)}")
    if agent_config.cannot_access:
        parts.append(
            f"CANNOT access: {', '.join(agent_config.cannot_access)}"
        )
    parts.append(f"Shell access: {agent_config.shell_access}\n")

    # Always-loaded skills (full content)
    parts.append("## Core Skills (always loaded)\n")
    for skill_path in agent_config.skills_always:
        content = load_skill_content(workspace, skill_path)
        if content:
            parts.append(f"### {skill_path}\n{content}\n")

    # Available skills (menu — names and descriptions only)
    if agent_config.skills_available:
        parts.append(
            "## Available Skills\n"
            "The following skills are available to you. "
            "To activate a skill, request it by name and I will load its full content.\n"
        )
        for skill_path in agent_config.skills_available:
            summary = load_skill_summary(workspace, skill_path)
            if summary:
                parts.append(summary)
        parts.append("")

    return "\n".join(parts)


def assemble_memory(
    config: FactoryConfig,
    agent_config: AgentConfig,
) -> str:
    """Load the agent's memory context.

    Loads: private MEMORY.md, today/yesterday daily logs,
    shared KNOWLEDGE.md and PROJECTS.md.
    """
    workspace = config.workspace
    parts: list[str] = []

    # Private memory
    private_path = workspace / agent_config.memory_private
    if private_path.exists():
        content = private_path.read_text().strip()
        if content:
            parts.append(f"## Your Private Memory\n\n{content}\n")

    # Daily logs — today and yesterday
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    daily_dir = workspace / agent_config.memory_daily

    for date_str, label in [(today, "Today"), (yesterday, "Yesterday")]:
        log_path = daily_dir / f"{date_str}.md"
        if log_path.exists():
            content = log_path.read_text().strip()
            if content:
                parts.append(f"## {label}'s Daily Log ({date_str})\n\n{content}\n")

    # Shared knowledge
    knowledge_path = workspace / "memory" / "shared" / "KNOWLEDGE.md"
    if knowledge_path.exists():
        content = knowledge_path.read_text().strip()
        if content:
            parts.append(f"## Shared Knowledge\n\n{content}\n")

    # Project status
    projects_path = workspace / "memory" / "shared" / "PROJECTS.md"
    if projects_path.exists():
        content = projects_path.read_text().strip()
        if content:
            parts.append(f"## Project Status\n\n{content}\n")

    return "\n".join(parts)


def assemble_context(
    config: FactoryConfig,
    agent_config: AgentConfig,
    task_content: str | None = None,
    message: str | None = None,
    is_heartbeat: bool = False,
) -> tuple[str, list[dict], str]:
    """Assemble full context for an agent invocation.

    Returns:
        (system_prompt, messages, context_bar)

    The system prompt includes identity, skills, access control.
    Messages include memory, task content, and/or user message.
    context_bar is the visual budget indicator.
    """
    timestamp = datetime.now()
    system_prompt = assemble_system_prompt(config, agent_config, timestamp)
    memory = assemble_memory(config, agent_config)

    # Build the user message(s)
    user_parts: list[str] = []

    if memory:
        user_parts.append(memory)

    if is_heartbeat and not task_content and not message:
        user_parts.append(
            f"It is {timestamp.isoformat()}. This is a heartbeat check.\n"
            "Review your inbox and memory. Decide if anything needs your attention.\n"
            "If nothing needs doing, write NO_REPLY and exit."
        )
    elif task_content:
        user_parts.append(f"## Task\n\n{task_content}")
    elif message:
        user_parts.append(message)

    user_text = "\n\n".join(user_parts)
    messages = [{"role": "user", "content": user_text}]

    # Context budget estimation
    total_chars = len(system_prompt) + len(user_text)
    total_tokens = estimate_tokens(total_chars.__str__()) + total_chars // CHARS_PER_TOKEN
    # Simpler estimation
    total_tokens = estimate_tokens(system_prompt + user_text)
    max_tokens = MODEL_CONTEXT_WINDOWS.get(agent_config.model, 200_000)
    pct = (total_tokens / max_tokens) * 100
    context_bar = build_context_bar(pct)

    return system_prompt, messages, context_bar
