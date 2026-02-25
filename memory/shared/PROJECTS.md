# Project Status

## Factory Infrastructure (ongoing)

Factory internal improvements that go through the spec → build → verify pipeline. Tracked here by spec name.

### multi-cli-backend-support
**Status:** Complete (verified 2026-02-25, 9/10)
**Scope:** Refactored `llm.py` into a multi-backend dispatcher. Extracted `backends/anthropic.py` (Claude Code CLI) and added `backends/kimi.py` (kimi-cli). Context assembly, ACL injection, and governance remain in dispatcher (backend-agnostic). `provider:` field in agents.yaml selects backend. `backends/capabilities.md` documents capability matrix.
**Minor observation:** `anthropic.py` carries a dead variable from the original code (cosmetic, pre-existing, non-functional).

### no-ephemeral-suggestions
**Status:** Complete (verified 2026-02-25, 9/10)
**Scope:** Replaced dead-end `category: observation` path in needs.md with structured `specs/factory-internal/` lifecycle. Added `factory triage` command (list/promote/dismiss). Kernel now auto-promotes observation entries from needs.md and extracts signal phrases from prose. 4th GC pass (`cleanup-factory-internal`). `factory status` shows Factory Internal section. `factory needs` no longer shows observations.
**Minor observation:** Fallback text extraction (non-standard needs.md entries) truncates body at 300 chars; full text preserved in source needs.md.

---

## hello-world-python

**Status:** Complete (verified 2026-02-25)
**Location:** `projects/hello-world-python/hello_world.py`
**Purpose:** End-to-end pipeline validation — first full traversal of spec → build → verify.
**Outcome:** Satisfaction score 10/10. All six verification criteria passed. Pipeline confirmed functional.
