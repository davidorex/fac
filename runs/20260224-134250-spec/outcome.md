# Outcome

Heartbeat complete. Summary:

**Inbox:** 4 items — 2 stale (`inbox-cleanup-convention`, `failure-learning-gap`), 2 new.

**Work done:** Specced and promoted 2 new NLSpecs to `specs/ready/`:

1. **task-review-cleanup** — Post-execution cleanup for `tasks/review/`, removing stale files that already exist in `tasks/verified/` or `tasks/failed/`. Direct analog of the existing `spec-pipeline-cleanup`. Adds `factory cleanup-tasks` CLI command. Currently 4 stale files in `tasks/review/` that this would clean.

2. **failed-task-lifecycle** — Adds `tasks/resolved/` directory to distinguish open vs. addressed failures. Automatic resolution after successful rebuilds (post-Verifier hook). Manual resolution via `factory resolve {task-name} --reason "..."` for failures resolved outside the pipeline. Currently `self-review-loop.md` and `seed-skill-gaps.v1.md` in `tasks/failed/` are resolved but indistinguishable from open failures.

**Stale inbox items** (`inbox-cleanup-convention`, `failure-learning-gap`) persist — they'll be cleaned when `spec-pipeline-cleanup` implementation goes live, or by human/operator intervention.
