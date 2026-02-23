"""Access control enforcement for agent filesystem operations."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from .config import AgentConfig


class AccessDenied(Exception):
    """Raised when an agent attempts an unauthorized filesystem operation."""

    def __init__(self, agent: str, operation: str, path: str, reason: str):
        self.agent = agent
        self.operation = operation
        self.path = path
        self.reason = reason
        super().__init__(
            f"ACCESS DENIED: {agent} cannot {operation} {path}. Reason: {reason}."
        )


def _normalize(path: str) -> str:
    """Normalize a path for prefix matching — strip leading slashes, ensure trailing slash for dirs."""
    return str(PurePosixPath(path)).strip("/")


def _path_matches_rule(path_norm: str, rule: str) -> bool:
    """Check if a normalized path matches a rule (prefix match).

    Rules like 'tasks/research/' match 'tasks/research/foo.md'.
    Rules like 'scenarios/*/satisfaction.md' match glob-style patterns.
    """
    rule_norm = _normalize(rule)

    # Handle glob patterns like scenarios/*/satisfaction.md
    if "*" in rule_norm:
        parts_rule = rule_norm.split("/")
        parts_path = path_norm.split("/")
        if len(parts_path) < len(parts_rule):
            return False
        for rp, pp in zip(parts_rule, parts_path):
            if rp == "*":
                continue
            if rp != pp:
                return False
        return len(parts_path) == len(parts_rule)

    # Prefix match — rule 'tasks/research/' matches 'tasks/research/foo.md'
    return path_norm == rule_norm or path_norm.startswith(rule_norm + "/") or path_norm.startswith(rule_norm)


def check_access(
    agent_config: AgentConfig,
    workspace: Path,
    operation: str,
    target_path: str,
) -> None:
    """Enforce access control for a filesystem operation.

    Args:
        agent_config: The agent's configuration with access rules.
        workspace: The workspace root path.
        operation: 'read' or 'write'.
        target_path: The path being accessed (relative to workspace or absolute).

    Raises:
        AccessDenied: If the operation is not permitted.
    """
    # Resolve to relative path within workspace
    abs_path = Path(target_path)
    if abs_path.is_absolute():
        try:
            rel = abs_path.relative_to(workspace)
        except ValueError:
            raise AccessDenied(
                agent_config.name,
                operation,
                target_path,
                "path is outside the workspace",
            )
        path_str = str(rel)
    else:
        path_str = target_path

    path_norm = _normalize(path_str)

    # universe/ is always read-only
    if path_norm.startswith("universe") and operation == "write":
        raise AccessDenied(
            agent_config.name,
            operation,
            target_path,
            "universe/ is read-only for all agents",
        )

    # agents.yaml is always read-only
    if path_norm == "agents.yaml" and operation == "write":
        raise AccessDenied(
            agent_config.name,
            operation,
            target_path,
            "agents.yaml is read-only — only the human edits this",
        )

    # Check cannot_access first — these are absolute denials
    for denied in agent_config.cannot_access:
        if _path_matches_rule(path_norm, denied):
            raise AccessDenied(
                agent_config.name,
                operation,
                target_path,
                f"cannot_access rule: {denied}",
            )

    # Check operation-specific rules
    if operation == "read":
        rules = agent_config.can_read
        # universe/ is always readable
        if path_norm.startswith("universe"):
            return
        # agents.yaml is always readable
        if path_norm == "agents.yaml":
            return
        # Own memory is always readable
        if path_norm.startswith(f"memory/{agent_config.name}") or path_norm.startswith(
            f"memory/daily/{agent_config.name}"
        ):
            return
    elif operation == "write":
        rules = agent_config.can_write
    else:
        raise ValueError(f"Unknown operation: {operation}")

    for rule in rules:
        if _path_matches_rule(path_norm, rule):
            return

    raise AccessDenied(
        agent_config.name,
        operation,
        target_path,
        f"not in {operation} allowlist",
    )
