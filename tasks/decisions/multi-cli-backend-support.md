# Decisions: multi-cli-backend-support

### 7.1 Governance hook gap for non-Claude backends
- status: resolved
- decided-by: operator
- decided-at: 2026-02-25T07:33:36
- answer: b
- reversibility: low
- impact: governance

### 7.1 Governance hook gap for non-Claude backends
- reversibility: low
- impact: governance
- status: open

**Context:** The factory currently relies on Claude Code's hook system (PreToolUse, PostToolUse, UserPromptSubmit) for governance enforcement — mandate checking, cleanup passes, etc. Based on prior research, kimi-cli does not appear to have an equivalent hook system.

**Options:**
- **(a) Accept the gap.** Kimi-backed agents run without hook-based governance. Acceptable for low-risk agents (e.g., researcher doing web lookups), documented as a known limitation. Governance for these agents relies on system prompt instructions + post-run verification.
- **(b) Move governance logic into the runtime dispatcher.** Before/after calling the backend, the dispatcher runs the equivalent checks that hooks would have run. This means reimplementing hook logic as Python code in the runtime — more work, but uniform governance.
- **(c) Defer kimi backend until kimi-cli adds hooks.** Wait for parity. Blocks the cost-management benefit.

**Recommendation:** (a) for initial implementation, with a seam that allows (b) later. Document the governance gap per-backend in a capabilities matrix.

### 7.2 Output streaming format
- status: auto-resolved
- decided-by: kernel
- decided-at: 2026-02-25T07:27:58
- answer: Start with (a) to unblock the backend, add (b) as a follow-up if kimi-cli supports it. The backend interface already returns a string — text-only fits naturally.
- reversibility: high
- impact: implementation

### 7.2 Output streaming format
- reversibility: high
- impact: implementation
- status: open

**Context:** Claude Code emits `stream-json` events. Kimi-cli's output format is not yet confirmed on disk (research brief lost). Two approaches:

**Options:**
- **(a) Text-only mode.** Run kimi-cli in print mode (equivalent of `-p`), capture final output. No live streaming. Simpler, but operator has no visibility during long runs.
- **(b) Streaming mode.** If kimi-cli supports a streaming output format, parse its events and translate them to the factory's terminal display format. Full live visibility, but requires implementing a kimi-specific event parser.

**Recommendation:** Start with (a) to unblock the backend, add (b) as a follow-up if kimi-cli supports it. The backend interface already returns a string — text-only fits naturally.

### 7.3 Model name validation
- status: auto-resolved
- decided-by: kernel
- decided-at: 2026-02-25T07:27:58
- answer: (a). Model names evolve faster than a validation list would be maintained. The backend CLI's own error is sufficient feedback.
- reversibility: high
- impact: implementation

### 7.3 Model name validation
- reversibility: high
- impact: implementation
- status: open

**Context:** Should the runtime validate that a model name is appropriate for its declared provider? (e.g., reject `provider: kimi` + `model: claude-opus-4-6`?)

**Options:**
- **(a) No validation.** Pass model strings through to the backend. Let the backend CLI fail with its own error if the model is invalid. Simpler, fewer things to maintain.
- **(b) Soft validation.** Each backend registers a list of known model names. Runtime warns on mismatch but still attempts the run. Catches typos without being brittle.

**Recommendation:** (a). Model names evolve faster than a validation list would be maintained. The backend CLI's own error is sufficient feedback.
