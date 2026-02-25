"""Backend registry for factory agent execution.

Maps provider names (as declared in agents.yaml) to backend modules.
Each backend module must implement run_agent() and _find_cli().

Adding a new backend:
  1. Create backends/{name}.py implementing run_agent() and _find_cli()
  2. Add an entry to BACKENDS below
  3. Update backends/capabilities.md with the new backend's capability row
"""

from __future__ import annotations

from typing import Any


# Registry is populated lazily on first get_backend() call to avoid
# circular imports at module load time.
_REGISTRY: dict[str, Any] | None = None


def _build_registry() -> dict[str, Any]:
    from . import anthropic, kimi
    return {
        "anthropic": anthropic,
        "kimi": kimi,
    }


def get_backend(provider: str) -> Any:
    """Return the backend module for the given provider string.

    Raises ValueError with a clear message listing available backends
    if the provider is unknown. This surfaces at dispatch time so the
    operator sees an actionable error immediately.
    """
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _build_registry()

    if provider not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY.keys()))
        raise ValueError(
            f"Unknown provider '{provider}'. Available backends: {available}"
        )

    return _REGISTRY[provider]


def list_providers() -> list[str]:
    """Return the list of registered provider names."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _build_registry()
    return list(_REGISTRY.keys())
