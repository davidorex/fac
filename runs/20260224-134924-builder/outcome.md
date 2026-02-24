# Outcome

Both specs are built and in `tasks/review/`. Summary:

**task-review-cleanup** — `run_task_review_cleanup(workspace, dry_run)` added to `cli.py`. Scans `tasks/review/` for files with exact-name matches in `tasks/verified/` or `tasks/failed/` (active slot only; versioned `.v{N}.md` excluded via regex). `factory cleanup-tasks [--dry-run]` command added. Hooked into `run` post-execution after spec pipeline cleanup (every agent). Ran live: removed the 4 stale review files. Idempotency and versioned-only non-match cases confirmed.

**failed-task-lifecycle** — `tasks/resolved/` created (factory init updated). `resolve_completed_failures(workspace)` automatically moves versioned/active failure reports to `tasks/resolved/` when the task is in `tasks/verified/`, appending `## Resolution / resolved_by: rebuild`. `resolve_task(workspace, task_name, reason)` handles manual resolution. `factory resolve {name} --reason "..."` CLI command added with git commit. `factory status` updated to show `tasks/resolved/`. Post-execution hook order: spec cleanup → task cleanup → failure resolution (verifier) → failure learning extraction (verifier). Applied during build: `seed-skill-gaps.v1.md` and `self-review-loop.md` moved to `tasks/resolved/` — `tasks/failed/` is now empty.
