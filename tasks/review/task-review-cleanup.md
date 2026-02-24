# Review: task-review-cleanup

spec_archive: specs/archive/task-review-cleanup.md
builder: builder
built: 2026-02-24T13:53

## What Was Built

Added `run_task_review_cleanup(workspace, dry_run=False) -> list[str]` to
`runtime/factory_runtime/cli.py`. Added `factory cleanup-tasks [--dry-run]`
CLI command. Hooked into `run` post-execution after spec pipeline cleanup,
before failure resolution.

The function scans `tasks/review/` for `.md` files with exact filename
matches in `tasks/verified/` or `tasks/failed/` (active, non-versioned slot
only — versioned `.v{N}.md` files are excluded via regex). On match, removes
from `tasks/review/` and logs the deletion with the downstream directory name.

The `factory cleanup-tasks` CLI wraps the function with dry-run prefix
substitution identical to `cleanup-specs`.

## Verification Criteria Check

- [x] `factory cleanup-tasks --dry-run` lists the 4 stale files without deleting
- [x] `factory cleanup-tasks` (live) removes all 4 stale files (already run as
      part of build to put workspace in correct state)
- [x] Idempotent: re-running finds 0 deletions
- [x] Versioned-only match: `test-fake-task.v1.md` in failed + `test-fake-task.md`
      in review → 0 deletions (versioned report not treated as match)
- [x] Unverified task (no downstream match) is untouched
- [x] Post-execution hook: ordered correctly after spec pipeline cleanup

## Deviations

None. Spec implemented as written.
