# tasks-research-done-has-no-cleanup-pass-for-comple

## What I'm Seeing
`tasks/research-done/` has no cleanup pass for completed briefs after the consuming spec is archived. `tasks/research-done/spec-kimi-cli-interface-v2.md` persists despite multi-cli-backend-support being in `specs/archive/` and `tasks/verified/`. The `cleanup-research` GC pass only cleans upstream (removes `tasks/research/` requests when `tasks/research-done/` exists). It does not clean downstream (remove `tasks/research-done/` briefs when no spec in `inbox/`, `drafting/`, or `ready/` references them). Same architectural class as the reviewer's NEED-R002 observation about `tasks/decisions/` — both are "consumed artifacts persist after their consumer is archived."

## What I Want to See
This observation should be addressed.
