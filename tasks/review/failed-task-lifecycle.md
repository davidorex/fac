# Review: failed-task-lifecycle

spec_archive: specs/archive/failed-task-lifecycle.md
builder: builder
built: 2026-02-24T13:53

## What Was Built

1. **`tasks/resolved/` directory** — created with `.gitkeep`. `factory init`
   updated to create it alongside other task directories.

2. **`resolve_completed_failures(workspace)`** — scans `tasks/verified/` and
   for each verified task moves matching files from `tasks/failed/` (active
   `{name}.md` and all versioned `{name}.v{N}.md`) to `tasks/resolved/`,
   appending `## Resolution` section (resolved_by: rebuild).

3. **`resolve_task(workspace, task_name, reason)`** — pure logic for manual
   resolution. Moves active + versioned failure reports, appending
   `## Resolution` section (resolved_by: manual). Returns (exit_code, message).

4. **`factory resolve {task-name} --reason "..."`** — CLI command wrapping
   `resolve_task`, commits state transition to git.

5. **`factory status`** — `tasks/resolved` added to pipeline display.

6. **Post-execution hook ordering** — `run` command now sequences:
   spec cleanup → task review cleanup → failure resolution (verifier) →
   failure learning extraction (verifier).

## Verification Criteria Check

- [x] `seed-skill-gaps.v1.md` moved to `tasks/resolved/seed-skill-gaps.v1.md`
      with `## Resolution / resolved_by: rebuild` — done during build
- [x] `factory resolve self-review-loop --reason "..."` moved
      `tasks/failed/self-review-loop.md` to `tasks/resolved/` with reason —
      done during build (verified correct `## Resolution` section appended)
- [x] `factory resolve` without `--reason` → Click raises MissingParameter
      (required option) and exits non-zero
- [x] `factory resolve nonexistent-task --reason "test"` → exit 1 with
      "No failure report found" message
- [x] `factory status` will show `tasks/resolved` in pipeline display
- [x] `factory init` creates `tasks/resolved/`
- [x] `tasks/failed/` now contains only genuinely unresolved failures (currently empty)

## Deviations

None. Spec implemented as written.

## Note

Both `self-review-loop.md` and `seed-skill-gaps.v1.md` were resolved during
the build run itself (to validate functionality). `tasks/failed/` is now empty.
