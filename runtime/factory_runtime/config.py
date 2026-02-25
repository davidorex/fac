"""Load and validate agents.yaml configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from . import permissions as perms


@dataclass
class AgentConfig:
    name: str
    role: str
    model: str
    provider: str
    skills_always: list[str]
    skills_available: list[str]
    memory_private: str
    memory_daily: str
    can_read: list[str]
    can_write: list[str]
    cannot_access: list[str]
    heartbeat: str
    shell_access: str  # "full", "read_only", "none"


@dataclass
class FactoryConfig:
    workspace: Path
    agents: dict[str, AgentConfig] = field(default_factory=dict)
    permissions: perms.PermissionsModel | None = None
    project_dir: Path | None = None   # set when invoked from a .factory project
    project_name: str | None = None   # derived from project_dir basename


def find_project_marker() -> tuple[Path, Path] | None:
    """Walk upward from cwd looking for a .factory marker file.

    Returns (project_dir, workspace_path) if found, None otherwise.
    """
    current = Path.cwd()
    while current != current.parent:
        marker = current / ".factory"
        if marker.is_file():
            raw = yaml.safe_load(marker.read_text()) or {}
            ws = raw.get("workspace")
            if ws:
                ws_path = Path(ws)
                if ws_path.is_absolute() and (ws_path / "agents.yaml").exists():
                    return current, ws_path
            return None  # marker exists but invalid
        current = current.parent
    return None


def find_workspace() -> Path:
    """Find the factory workspace root.

    Resolution order:
    1. .factory marker in cwd or parent (project context)
    2. FACTORY_WORKSPACE env var
    3. Walk up from cwd looking for agents.yaml (direct factory context)
    """
    # Check for .factory project marker first
    project = find_project_marker()
    if project:
        return project[1]

    env_path = os.environ.get("FACTORY_WORKSPACE")
    if env_path:
        p = Path(env_path)
        if (p / "agents.yaml").exists():
            return p
        raise FileNotFoundError(
            f"FACTORY_WORKSPACE={env_path} does not contain agents.yaml"
        )

    # Walk up from cwd looking for agents.yaml
    current = Path.cwd()
    while current != current.parent:
        if (current / "agents.yaml").exists():
            return current
        current = current.parent

    raise FileNotFoundError(
        "No agents.yaml found. Run 'factory init-project' to register this directory, "
        "set FACTORY_WORKSPACE, or run from within a factory workspace."
    )


def load_config(workspace: Path | None = None) -> FactoryConfig:
    """Load and parse agents.yaml from the workspace root."""
    if workspace is None:
        workspace = find_workspace()

    config_path = workspace / "agents.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"agents.yaml not found at {config_path}")

    with open(config_path) as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    # Use the workspace path from config, resolved relative to the yaml file
    ws_path = Path(raw.get("workspace", str(workspace)))
    if not ws_path.is_absolute():
        ws_path = config_path.parent / ws_path

    config = FactoryConfig(workspace=ws_path)

    # Load Unix-style permissions model (optional overlay)
    config.permissions = perms.load(ws_path)

    # Populate project context if invoked from a .factory directory
    project = find_project_marker()
    if project:
        config.project_dir = project[0]
        config.project_name = project[0].name

    for name, agent_raw in raw.get("agents", {}).items():
        skills = agent_raw.get("skills", {})
        memory = agent_raw.get("memory", {})

        config.agents[name] = AgentConfig(
            name=name,
            role=agent_raw.get("role", ""),
            model=agent_raw.get("model", "claude-sonnet-4-5"),
            provider=agent_raw.get("provider", "anthropic"),
            skills_always=skills.get("always", []),
            skills_available=skills.get("available", []),
            memory_private=memory.get("private", f"memory/{name}/MEMORY.md"),
            memory_daily=memory.get("daily", f"memory/daily/{name}/"),
            can_read=agent_raw.get("can_read", []),
            can_write=agent_raw.get("can_write", []),
            cannot_access=agent_raw.get("cannot_access", []),
            heartbeat=agent_raw.get("heartbeat", "0 * * * *"),
            shell_access=agent_raw.get("shell_access", "none"),
        )

    return config
