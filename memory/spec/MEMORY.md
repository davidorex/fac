# Spec — Private Memory

## Active Specs

### multi-cli-backend-support
- **Status:** In `specs/ready/`, unblocked for Builder
- **All ambiguities resolved:**
  - 7.1 (governance): operator chose (b) — pre/post governance in dispatcher. Per-tool-call gap documented.
  - 7.2 (streaming): text-only for kimi initially. Auto-resolved.
  - 7.3 (model validation): no validation, pass-through. Auto-resolved.
- **Key architectural decisions baked into spec:**
  - Dispatcher owns context assembly + ACL + governance; backends own CLI invocation + output capture
  - Binary name `kimi-cli` (not `kimi`) to avoid alias conflict
  - Agent file + temp system prompt file required for each kimi invocation (no inline --system-prompt)
  - Backend function signature gets `system_prompt`/`user_prompt` params (dispatcher passes assembled prompts)
- **Research brief:** `tasks/research-done/spec-kimi-cli-interface-v2.md` — high confidence, empirically verified

## Learned: File Persistence Across Sessions

On 2026-02-25, discovered that file operations from a prior session (05:18 heartbeat) did not persist to disk despite being recorded in the daily log. The daily log itself persisted but the spec drafting file, research request, and research brief were all absent. Cause unknown. Mitigation: always verify disk state at the start of each heartbeat rather than trusting daily log records from prior sessions.
