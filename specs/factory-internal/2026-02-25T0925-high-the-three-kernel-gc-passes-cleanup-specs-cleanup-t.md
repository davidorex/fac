# the-three-kernel-gc-passes-cleanup-specs-cleanup-t
- severity: high
- status: open
- created: 2026-02-25T08:17
- source-agent: reviewer
- source-type: needs-promotion

## Observation
The three kernel GC passes (cleanup-specs, cleanup-tasks, cleanup-research) do not cover `tasks/decisions/`. Resolved decisions with verified tasks accumulate. `tasks/decisions/multi-cli-backend-support.md` is the first instance — all entries resolved, task verified, file still present. A `cleanup-d

## Context
Promoted from needs.md entry: NEED-R002: GC gap — tasks/decisions/ has no cleanup pass. Agent: reviewer. Source file: memory/reviewer/needs.md.
