"""Load and query app definitions from the apps/ directory.

Apps are declarative workflow definitions — the layer between the operator
and the kernel.  Each app is a YAML file in apps/ that declares pipeline
stages, dispatch rules, checkpoint types, and execution strategies.

The kernel reads app definitions to determine how work flows through the
system.  Multiple apps can coexist; they govern different parts of the
pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class PipelineStage:
    """A pipeline stage introduced by an app."""
    name: str
    dir: str
    producer: str
    consumer: list[str]


@dataclass
class Artifact:
    """An artifact an app produces on the bus."""
    name: str
    location: str
    contains: list[str]


@dataclass
class Checkpoint:
    """A checkpoint type declarable in plan artifacts."""
    name: str
    maps_to: str
    gate: str  # "soft" or "hard"
    description: str


@dataclass
class Strategy:
    """An execution strategy the kernel can select."""
    name: str
    condition: str
    dispatch: str  # "single-run", "run-per-segment", "sequential"
    pause_at: list[str]


@dataclass
class DispatchRule:
    """A dispatch rule mapping a stage to an agent."""
    name: str
    agent: str
    input: str
    output: str
    validate_with: str | None = None
    max_validation_rounds: int = 1
    strategy: str | None = None


@dataclass
class ConfigOption:
    """An operator-tunable configuration option."""
    name: str
    type: str  # "enum", "bool"
    default: Any = None
    values: list[str] | None = None
    description: str = ""
    affects: dict[str, dict[str, str]] | None = None


@dataclass
class AppDefinition:
    """A complete app definition loaded from YAML."""
    name: str
    description: str
    path: Path
    stages: list[PipelineStage]
    artifacts: list[Artifact]
    checkpoints: list[Checkpoint]
    strategies: list[Strategy]
    dispatch: list[DispatchRule]
    config: list[ConfigOption]


def _parse_stages(raw: dict) -> list[PipelineStage]:
    """Parse pipeline.stages from raw YAML."""
    pipeline = raw.get("pipeline", {})
    stages_raw = pipeline.get("stages", [])
    stages = []
    for s in stages_raw:
        consumer = s.get("consumer", [])
        if isinstance(consumer, str):
            consumer = [consumer]
        stages.append(PipelineStage(
            name=s["name"],
            dir=s["dir"],
            producer=s.get("producer", ""),
            consumer=consumer,
        ))
    return stages


def _parse_artifacts(raw: dict) -> list[Artifact]:
    """Parse pipeline.artifacts from raw YAML."""
    pipeline = raw.get("pipeline", {})
    artifacts_raw = pipeline.get("artifacts", {})
    artifacts = []
    for name, a in artifacts_raw.items():
        artifacts.append(Artifact(
            name=name,
            location=a.get("location", ""),
            contains=a.get("contains", []),
        ))
    return artifacts


def _parse_checkpoints(raw: dict) -> list[Checkpoint]:
    """Parse checkpoints from raw YAML."""
    cp_raw = raw.get("checkpoints", {})
    checkpoints = []
    for name, c in cp_raw.items():
        checkpoints.append(Checkpoint(
            name=name,
            maps_to=c.get("maps_to", ""),
            gate=c.get("gate", "soft"),
            description=c.get("description", ""),
        ))
    return checkpoints


def _parse_strategies(raw: dict) -> list[Strategy]:
    """Parse strategies from raw YAML."""
    strat_raw = raw.get("strategies", {})
    strategies = []
    for name, s in strat_raw.items():
        pause = s.get("pause_at", [])
        if isinstance(pause, str):
            pause = [pause]
        strategies.append(Strategy(
            name=name,
            condition=s.get("condition", ""),
            dispatch=s.get("dispatch", "single-run"),
            pause_at=pause,
        ))
    return strategies


def _parse_dispatch(raw: dict) -> list[DispatchRule]:
    """Parse dispatch rules from raw YAML."""
    disp_raw = raw.get("dispatch", {})
    rules = []
    for name, d in disp_raw.items():
        rules.append(DispatchRule(
            name=name,
            agent=d.get("agent", ""),
            input=d.get("input", ""),
            output=d.get("output", ""),
            validate_with=d.get("validate_with"),
            max_validation_rounds=d.get("max_validation_rounds", 1),
            strategy=d.get("strategy"),
        ))
    return rules


def _parse_config(raw: dict) -> list[ConfigOption]:
    """Parse config options from raw YAML."""
    conf_raw = raw.get("config", {})
    options = []
    for name, c in conf_raw.items():
        options.append(ConfigOption(
            name=name,
            type=c.get("type", "bool"),
            default=c.get("default"),
            values=c.get("values"),
            description=c.get("description", ""),
            affects=c.get("affects"),
        ))
    return options


def load_app(path: Path) -> AppDefinition:
    """Load a single app definition from a YAML file."""
    with open(path) as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    return AppDefinition(
        name=raw.get("name", path.stem),
        description=raw.get("description", ""),
        path=path,
        stages=_parse_stages(raw),
        artifacts=_parse_artifacts(raw),
        checkpoints=_parse_checkpoints(raw),
        strategies=_parse_strategies(raw),
        dispatch=_parse_dispatch(raw),
        config=_parse_config(raw),
    )


def load_all(workspace: Path) -> list[AppDefinition]:
    """Load all app definitions from the apps/ directory.

    Returns an empty list if the directory doesn't exist or contains no
    YAML files.
    """
    apps_dir = workspace / "apps"
    if not apps_dir.is_dir():
        return []

    apps = []
    for path in sorted(apps_dir.glob("*.yaml")):
        apps.append(load_app(path))
    return apps


def find_app(apps: list[AppDefinition], name: str) -> AppDefinition | None:
    """Find an app by name."""
    for app in apps:
        if app.name == name:
            return app
    return None


def has_planning_stage(apps: list[AppDefinition]) -> PipelineStage | None:
    """Check if any loaded app declares a planning stage.

    Returns the first planning stage found, or None.  The kernel uses
    this to decide whether to route specs/ready/ through tasks/planning/
    before tasks/building/.
    """
    for app in apps:
        for stage in app.stages:
            if stage.name == "planning":
                return stage
    return None


def get_dispatch_rule(
    apps: list[AppDefinition], stage_name: str
) -> DispatchRule | None:
    """Get the dispatch rule for a named stage across all apps."""
    for app in apps:
        for rule in app.dispatch:
            if rule.name == stage_name:
                return rule
    return None


def get_strategies(apps: list[AppDefinition]) -> list[Strategy]:
    """Collect all execution strategies across apps."""
    strategies = []
    for app in apps:
        strategies.extend(app.strategies)
    return strategies
