# Builder — Private Memory

## Spec Lifecycle Protocol (established 2026-02-24)

When picking up a spec from `specs/ready/`:
1. **Copy** spec to `specs/archive/{name}.md` first — do not proceed if this fails
2. **Remove** from `specs/ready/` after archive is confirmed
3. **Implement** the spec
4. **Write** review task to `tasks/review/{name}.md` with `spec_archive: specs/archive/{name}.md` field

If `specs/archive/{name}.md` already exists, rename the existing file to `specs/archive/{name}.v{N}.md` (next integer N) before writing the new archive. Never delete specs.

## Completed Tasks

- `hello-world` — stdlib Python CLI greeting script, verified and in `tasks/verified/`
- `spec-lifecycle` — behavioral convention establishing the spec archive protocol
- `task-review-cleanup` — `run_task_review_cleanup` + `factory cleanup-tasks` in cli.py; in tasks/review/
- `failed-task-lifecycle` — `tasks/resolved/`, `resolve_completed_failures`, `factory resolve` in cli.py; in tasks/review/
