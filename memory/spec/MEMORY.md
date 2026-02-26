# Spec — Private Memory

## Completed Specs

### multi-cli-backend-support
- **Status:** Archived, verified 2026-02-25 (9/10)
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

### no-ephemeral-suggestions
- **Status:** Archived, verified 2026-02-25 (9/10)
- **Both ambiguities auto-resolved (soft gates):**
  - §7.1: kernel-assigned severity via keyword heuristics (not agent-assigned)
  - §7.2: kernel-mediated writes — agents write to needs.md, kernel promotes to `specs/factory-internal/`. No agents.yaml changes.
- **Key architectural decisions baked into spec:**
  - `specs/factory-internal/` directory with `{YYYY-MM-DDTHHMM}-{severity}-{slug}.md` naming
  - Kernel safety net writes directly to factory-internal (not needs.md) for observations
  - Kernel post-run pass promotes needs.md `category: observation` entries to factory-internal
  - `factory triage` command for operator lifecycle management (promote/dismiss)
  - `factory status` shows severity-grouped counts
  - `factory needs` stops displaying observations
  - One-time migration of existing observation entries
  - `cleanup-factory-internal` GC pass for promoted/dismissed files

## Learned: File Persistence Across Sessions

On 2026-02-25, discovered that file operations from a prior session (05:18 heartbeat) did not persist to disk despite being recorded in the daily log. The daily log itself persisted but the spec drafting file, research request, and research brief were all absent. Cause unknown. Mitigation: always verify disk state at the start of each heartbeat rather than trusting daily log records from prior sessions.

## Skill Usage Patterns

- **nlspec-format**: Used every spec run. Core to all output. Currently in `available` — should arguably be `always`.
- **decision-heuristic**: Used every spec run for §7 classification. Currently in `available` — should arguably be `always`.
- **domain-interview**: Never activated. Both intents processed so far were clear enough to spec without human interview.
- **decomposition**: Never activated. No spec has required parallel subagent work.
- **spec-patterns**: Referenced for framing. Minimal utility for factory-internal specs (only has CLI tool skeleton).
