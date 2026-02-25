# tasks-research-done-has-no-cleanup-pass-for-comple
- severity: low
- status: promoted
- promoted_to: specs/inbox/tasks-research-done-has-no-cleanup-pass-for-comple.md
- promoted_at: 2026-02-26T07:09:35
- created: 2026-02-25T20:48:00Z
- source-agent: spec
- source-type: needs-promotion

## Observation
`tasks/research-done/` has no cleanup pass for completed briefs after the consuming spec is archived. `tasks/research-done/spec-kimi-cli-interface-v2.md` persists despite multi-cli-backend-support being in `specs/archive/` and `tasks/verified/`. The `cleanup-research` GC pass only cleans upstream (removes `tasks/research/` requests when `tasks/research-done/` exists). It does not clean downstream (remove `tasks/research-done/` briefs when no spec in `inbox/`, `drafting/`, or `ready/` references them). Same architectural class as the reviewer's NEED-R002 observation about `tasks/decisions/` — both are "consumed artifacts persist after their consumer is archived."

## Context
Promoted from needs.md entry: spec-research-done-no-archival-gc. Agent: spec. Source file: memory/spec/needs.md.
