# Outcome

Implementation complete. Here's what was built:

**`runtime/factory_runtime/backends/`** — new package:
- `__init__.py` — registry: `get_backend("kimi")` → kimi module, clear error for unknown providers
- `common.py` — shared ANSI colors, `_short_path`, `_format_tool_use` (no longer duplicated)
- `anthropic.py` — Claude Code CLI logic extracted from old `llm.py`, same behavior
- `kimi.py` — kimi-cli backend: writes temp agent YAML + system prompt file per run, cleans up in `finally`, uses `--print --output-format text -p "prompt"` 
- `capabilities.md` — per-backend capability matrix with documented gaps

**`runtime/factory_runtime/llm.py`** — rewritten as dispatcher:
- Owns context assembly, ACL injection, backend selection
- `run_pre_governance()` — loads mandates from `~/.claude/mandates.jsonl`, injects into system_prompt before dispatch
- `run_post_governance()` — pass-through seam with run-log entry
- `validate_providers()` — startup binary check, returns warnings (non-blocking)

**`runtime/factory_runtime/cli.py`** — `factory run` now calls `validate_providers()` and shows `provider:` in the agent header.

Two friction points worth surfacing:

1. **Pyright can't resolve the backends package** at static analysis time (it's dynamically constructed). The `from .backends import get_backend` pattern causes `reportAttributeAccessIssue` warnings. Runtime works fine — this is a tooling limitation, not a code defect.

2. **kimi text-only mode means operator blindness during runs.** The streaming follow-up needs a separate stream-json parser (conversation-turn JSONL schema, not Claude's event-type schema). Worth prioritizing if kimi-backed agents run long tasks.
