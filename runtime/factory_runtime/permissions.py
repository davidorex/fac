"""Unix-style permissions for factory agents.

Maps agents to users, defines groups, assigns owner:group:mode to
resources, and provides enforcement and escalation policy.

When ``permissions.yaml`` is absent the system falls back to the flat
ACL model in ``agents.yaml`` (can_read / can_write / cannot_access).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Mode:
    """Parsed ``rwxrwxrwx`` mode bits (owner / group / other)."""

    owner_read: bool = False
    owner_write: bool = False
    owner_exec: bool = False
    group_read: bool = False
    group_write: bool = False
    group_exec: bool = False
    other_read: bool = False
    other_write: bool = False
    other_exec: bool = False

    @classmethod
    def from_string(cls, s: str) -> Mode:
        """Parse ``'rw-rw-r--'`` or ``'rwxrwxrwx'`` format."""
        if len(s) != 9:
            raise ValueError(f"Invalid mode string (need 9 chars): {s!r}")
        return cls(
            owner_read=s[0] == "r",
            owner_write=s[1] == "w",
            owner_exec=s[2] == "x",
            group_read=s[3] == "r",
            group_write=s[4] == "w",
            group_exec=s[5] == "x",
            other_read=s[6] == "r",
            other_write=s[7] == "w",
            other_exec=s[8] == "x",
        )

    def __str__(self) -> str:
        chars = [
            "r" if self.owner_read else "-",
            "w" if self.owner_write else "-",
            "x" if self.owner_exec else "-",
            "r" if self.group_read else "-",
            "w" if self.group_write else "-",
            "x" if self.group_exec else "-",
            "r" if self.other_read else "-",
            "w" if self.other_write else "-",
            "x" if self.other_exec else "-",
        ]
        return "".join(chars)


@dataclass
class Resource:
    """A resource with ownership and Unix-style mode."""

    path: str   # may contain ``{agent}`` template
    owner: str  # agent name, ``root``, or ``{agent}``
    group: str  # group name or ``{agent}``
    mode: Mode


@dataclass
class PermissionsModel:
    """The complete permissions model loaded from ``permissions.yaml``."""

    groups: dict[str, list[str]]          # group_name → [agent_names]
    resources: list[Resource]
    escalation: dict[str, list[str]]      # group_name → [change_classes]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load(workspace: Path) -> PermissionsModel | None:
    """Load ``permissions.yaml`` from *workspace*.  Returns ``None`` if absent."""
    perms_path = workspace / "permissions.yaml"
    if not perms_path.exists():
        return None

    with open(perms_path) as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    groups: dict[str, list[str]] = raw.get("groups", {})

    resources: list[Resource] = []
    for path, spec in raw.get("resources", {}).items():
        mode = Mode.from_string(spec["mode"])
        resources.append(
            Resource(
                path=str(path),
                owner=spec.get("owner", "root"),
                group=spec.get("group", "root"),
                mode=mode,
            )
        )

    escalation: dict[str, list[str]] = raw.get("escalation", {})

    return PermissionsModel(
        groups=groups,
        resources=resources,
        escalation=escalation,
    )


# ---------------------------------------------------------------------------
# Group resolution
# ---------------------------------------------------------------------------


def agent_groups(model: PermissionsModel, agent: str) -> list[str]:
    """Return all groups *agent* belongs to (including its own eponymous group)."""
    groups = [agent]
    for group_name, members in model.groups.items():
        if agent in members:
            groups.append(group_name)
    return groups


# ---------------------------------------------------------------------------
# Resource matching
# ---------------------------------------------------------------------------


def _normalize(path: str) -> str:
    return str(PurePosixPath(path)).strip("/")


def _expand(template: str, agent: str) -> str:
    return template.replace("{agent}", agent)


def find_resource(
    model: PermissionsModel, path: str, agent: str
) -> Resource | None:
    """Find the most-specific resource rule matching *path* for *agent*.

    Templates like ``memory/{agent}/`` are expanded using *agent*.
    Returns a new ``Resource`` with templates expanded, or ``None``.
    """
    path_norm = _normalize(path)
    best: Resource | None = None
    best_len = -1

    for res in model.resources:
        res_path = _expand(res.path, agent)
        res_norm = _normalize(res_path)

        # Exact match or prefix match
        if path_norm == res_norm or path_norm.startswith(res_norm + "/"):
            if len(res_norm) > best_len:
                best = Resource(
                    path=res_path,
                    owner=_expand(res.owner, agent),
                    group=_expand(res.group, agent),
                    mode=res.mode,
                )
                best_len = len(res_norm)

    return best


# ---------------------------------------------------------------------------
# Permission check
# ---------------------------------------------------------------------------


def check(
    model: PermissionsModel,
    agent: str,
    operation: str,
    path: str,
) -> tuple[bool, str]:
    """Check whether *agent* has *operation* (``read`` / ``write``) access to *path*.

    Returns ``(allowed, reason)``.
    """
    resource = find_resource(model, path, agent)
    if resource is None:
        return False, f"no resource rule for {path}"

    groups = agent_groups(model, agent)
    is_owner = resource.owner == agent
    is_in_group = resource.group in groups

    if operation == "read":
        if is_owner and resource.mode.owner_read:
            return True, f"owner read ({resource.path})"
        if is_in_group and resource.mode.group_read:
            return True, f"group:{resource.group} read ({resource.path})"
        if resource.mode.other_read:
            return True, f"other read ({resource.path})"
        return (
            False,
            f"denied read on {resource.path} "
            f"[{resource.mode}] owner={resource.owner} "
            f"group={resource.group} agent_groups={groups}",
        )

    if operation == "write":
        if is_owner and resource.mode.owner_write:
            return True, f"owner write ({resource.path})"
        if is_in_group and resource.mode.group_write:
            return True, f"group:{resource.group} write ({resource.path})"
        if resource.mode.other_write:
            return True, f"other write ({resource.path})"
        return (
            False,
            f"denied write on {resource.path} "
            f"[{resource.mode}] owner={resource.owner} "
            f"group={resource.group} agent_groups={groups}",
        )

    return False, f"unknown operation: {operation}"


# ---------------------------------------------------------------------------
# Escalation
# ---------------------------------------------------------------------------


def can_escalate(
    model: PermissionsModel, agent: str, change_class: str
) -> bool:
    """Return ``True`` if *agent*'s groups authorize escalation for *change_class*."""
    groups = agent_groups(model, agent)
    for grp in groups:
        if change_class in model.escalation.get(grp, []):
            return True
    return False


# ---------------------------------------------------------------------------
# Effective access computation
# ---------------------------------------------------------------------------


def effective_access(
    model: PermissionsModel, agent: str, all_agents: list[str] | None = None
) -> tuple[list[str], list[str]]:
    """Compute effective ``can_read`` / ``can_write`` lists for *agent*.

    Iterates all resources, expands ``{agent}`` templates, and returns
    the paths the agent can read / write according to the mode bits.

    When *all_agents* is provided, templated resources like
    ``memory/{agent}/`` are expanded for every agent (the calling agent
    still only sees paths it has permission for).  When absent,
    templates are expanded only for *agent* itself.
    """
    can_read: list[str] = []
    can_write: list[str] = []

    agents_to_expand = all_agents or [agent]
    groups = agent_groups(model, agent)

    for res in model.resources:
        # Determine which expansions to try
        if "{agent}" in res.path:
            expand_list = agents_to_expand
        else:
            expand_list = [""]  # no expansion needed

        for expand_agent in expand_list:
            if expand_agent:
                res_path = _expand(res.path, expand_agent)
                owner = _expand(res.owner, expand_agent)
                group = _expand(res.group, expand_agent)
            else:
                res_path = res.path
                owner = res.owner
                group = res.group

            is_owner = owner == agent
            is_in_group = group in groups

            # Read
            if (
                (is_owner and res.mode.owner_read)
                or (is_in_group and res.mode.group_read)
                or res.mode.other_read
            ):
                can_read.append(res_path)

            # Write
            if (
                (is_owner and res.mode.owner_write)
                or (is_in_group and res.mode.group_write)
                or res.mode.other_write
            ):
                can_write.append(res_path)

    return can_read, can_write


# ---------------------------------------------------------------------------
# Config-edit application (kernel sudo)
# ---------------------------------------------------------------------------


def apply_skill_placement(
    yaml_text: str, target_agent: str, skill: str,
    from_list: str, to_list: str,
) -> str:
    """Move *skill* between ``always`` / ``available`` for *target_agent*.

    Operates on the raw text of ``agents.yaml`` using line-level
    replacement to preserve formatting, comments, and inline list style.

    Returns the modified text.  Raises ``ValueError`` on parse failures.
    """
    lines = yaml_text.split("\n")

    # Find agent section boundaries
    agent_start: int | None = None
    agent_end = len(lines)

    for i, line in enumerate(lines):
        stripped = line.rstrip()
        # Agent names are at 2-space indent: "  builder:"
        if stripped == f"  {target_agent}:":
            agent_start = i
        elif agent_start is not None and i > agent_start + 1:
            # Another agent starts at 2-space indent (not deeper)
            if re.match(r"^  [a-z]", stripped):
                agent_end = i
                break

    if agent_start is None:
        raise ValueError(f"Agent '{target_agent}' not found in agents.yaml")

    # Find from_list and to_list lines within agent section
    from_idx: int | None = None
    to_idx: int | None = None

    for i in range(agent_start, agent_end):
        stripped = lines[i].strip()
        if stripped.startswith(f"{from_list}:"):
            from_idx = i
        elif stripped.startswith(f"{to_list}:"):
            to_idx = i

    if from_idx is None:
        raise ValueError(
            f"'{from_list}' list not found for {target_agent}"
        )
    if to_idx is None:
        raise ValueError(
            f"'{to_list}' list not found for {target_agent}"
        )

    # Parse and modify from_list line: remove the skill
    from_match = re.match(r"^(\s+\w+:\s*\[)(.*?)(\].*)$", lines[from_idx])
    if not from_match:
        raise ValueError(
            f"Cannot parse {from_list} line: {lines[from_idx]!r}"
        )
    from_items = [s.strip() for s in from_match.group(2).split(",") if s.strip()]
    if skill not in from_items:
        raise ValueError(
            f"'{skill}' not in {target_agent}'s {from_list} list"
        )
    from_items.remove(skill)
    lines[from_idx] = (
        from_match.group(1)
        + ", ".join(from_items)
        + from_match.group(3)
    )

    # Parse and modify to_list line: add the skill
    to_match = re.match(r"^(\s+\w+:\s*\[)(.*?)(\].*)$", lines[to_idx])
    if not to_match:
        raise ValueError(
            f"Cannot parse {to_list} line: {lines[to_idx]!r}"
        )
    to_items = [s.strip() for s in to_match.group(2).split(",") if s.strip()]
    to_items.append(skill)
    lines[to_idx] = (
        to_match.group(1)
        + ", ".join(to_items)
        + to_match.group(3)
    )

    return "\n".join(lines)
