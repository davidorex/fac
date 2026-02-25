# Reviewer — Human Action Needed

## NEED-R001: Universe reference doc has 5 inaccuracies
- category: observation
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T0925-high-universe-reference-tool-capabilities-md-has-5-empi.md
- filed: 2026-02-25T08:17
- source: tasks/research-done/spec-kimi-cli-interface-v2.md

`universe/reference/tool-capabilities.md` has 5 empirically verified inaccuracies about kimi-cli (detailed in research brief). Universe/ is read-only — only the operator can correct these. Per values.md: "Your tools evolve. So do you" — stale reference docs undermine tool awareness.

## NEED-R002: GC gap — tasks/decisions/ has no cleanup pass
- category: observation
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T0925-high-the-three-kernel-gc-passes-cleanup-specs-cleanup-t.md
- filed: 2026-02-25T08:17

The three kernel GC passes (cleanup-specs, cleanup-tasks, cleanup-research) do not cover `tasks/decisions/`. Resolved decisions with verified tasks accumulate. `tasks/decisions/multi-cli-backend-support.md` is the first instance — all entries resolved, task verified, file still present. A `cleanup-decisions` pass would remove decision files when the corresponding spec is archived and the task is verified.

## NEED-R003: 4 agents never write daily logs
- category: observation
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T0925-low-builder-verifier-librarian-and-operator-have-empty.md
- filed: 2026-02-25T08:17

Builder, verifier, librarian, and operator have empty daily log directories. Builder and verifier both ran on 2026-02-25 but wrote no logs. The context-discipline skill mandates daily log writes on task completion. Either the skill instruction is not reaching these agents effectively or they are deprioritizing it. This degrades traceability (values.md: "Every artifact should be traceable").
