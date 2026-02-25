# Task: multi-cli-backend-support

**Status:** Ready for verification
**Spec:** specs/archive/multi-cli-backend-support.md
**Builder notes:** tasks/review/multi-cli-backend-support.builder-notes.md
**Commit:** b8e2b2c

## Summary

Backend dispatch abstraction implemented. `llm.py` is now a dispatcher;
Claude Code and kimi-cli backends live in `runtime/factory_runtime/backends/`.
Governance pre/post hooks implemented. Startup validation added to `factory run`.

## Files changed

- `runtime/factory_runtime/llm.py` — rewritten as dispatcher
- `runtime/factory_runtime/backends/__init__.py` — registry (new)
- `runtime/factory_runtime/backends/common.py` — shared utilities (new)
- `runtime/factory_runtime/backends/anthropic.py` — Claude Code backend (new, extracted)
- `runtime/factory_runtime/backends/kimi.py` — kimi-cli backend (new)
- `runtime/factory_runtime/backends/capabilities.md` — capability matrix (new)
- `runtime/factory_runtime/cli.py` — validate_providers call + provider in run header

## Verification checkpoints

1. Set `provider: kimi` on an agent → `factory run {agent}` → executes via kimi-cli
2. `provider: anthropic` (or absent) → live streaming behavior unchanged
3. `provider: nonexistent` → error names available backends
4. Missing kimi-cli → startup warning, anthropic agents unaffected
5. Mandate text present in kimi temp agent file system prompt
6. Post-governance event in run log after kimi run
7. No temp files left in /tmp after kimi run (including after error)
8. No new pip dependencies introduced
