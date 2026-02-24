# failed-task-lifecycle

## Overview

When a task fails verification, its failure report lands in `tasks/failed/` and has no defined lifecycle after that. Three resolution paths exist in practice but none are codified:

1. **Rebuild** — `factory rebuild` requeues the spec and versions the failure report to `.v{N}.md`. If the rebuild succeeds through the full pipeline (Verifier passes), the versioned failure report sits in `tasks/failed/` indefinitely with no indication it was resolved.
2. **Human intervention** — the human resolves the blocker outside the pipeline (e.g., `self-review-loop` failed because the reviewer agent wasn't in `agents.yaml`; human added it). The failure report sits in `tasks/failed/` forever with no way to mark it resolved.
3. **Unresolvable** — no path exists to acknowledge a failure that cannot or should not be fixed.

The result: `tasks/failed/` accumulates resolved and unresolved failures with no distinction between them. The reviewer agent reads this directory for failure patterns but cannot tell which failures are still open. Currently `tasks/failed/` contains `self-review-loop.md` (resolved by human action) and `seed-skill-gaps.v1.md` (versioned by rebuild) — one resolved, one historical, both presenting as active failures.

This spec adds a `tasks/resolved/` directory and conventions for closing out failed tasks, so `tasks/failed/` contains only open failures that need attention.

## Behavioral Requirements

### New directory: `tasks/resolved/`

1. **`tasks/resolved/` is the archive for addressed failures.** Files in this directory are failure reports that were resolved — by rebuild, human intervention, or intentional closure. The directory is a terminal state for failure reports; files are not moved out of it.

2. **`factory init` creates `tasks/resolved/`** alongside the other task directories.

### Automatic resolution after successful rebuild

3. **When the factory runtime finishes executing the Verifier**, it runs a failure resolution pass. For each task in `tasks/verified/`, the pass checks `tasks/failed/` for versioned failure reports matching the pattern `{task-name}.v{N}.md`. If any exist, they are moved to `tasks/resolved/`.

4. **Before moving a versioned failure report**, the runtime appends a `## Resolution` section to the file:
   ```markdown
   ## Resolution
   - resolved_by: rebuild
   - resolved_at: {ISO 8601 timestamp}
   - verified_task: tasks/verified/{task-name}.md
   ```

5. **The resolution pass also checks for active (non-versioned) failure reports** that match a verified task. If `tasks/failed/{task-name}.md` exists and `tasks/verified/{task-name}.md` also exists, the active failure report is moved to `tasks/resolved/` with the same resolution annotation. This handles cases where a failure was resolved without using `factory rebuild` (e.g., human re-ran the verifier after fixing a blocker).

### Manual resolution

6. **`factory resolve {task-name}` moves an active failure report from `tasks/failed/` to `tasks/resolved/`** for cases resolved outside the pipeline. The command requires a `--reason` flag explaining how the failure was resolved. The runtime appends a `## Resolution` section before moving:
   ```markdown
   ## Resolution
   - resolved_by: manual
   - resolved_at: {ISO 8601 timestamp}
   - reason: {value of --reason flag}
   ```

7. **`factory resolve` also moves any versioned failure reports** for the same task. If `tasks/failed/{task-name}.v1.md`, `tasks/failed/{task-name}.v2.md`, etc., exist, they are all moved to `tasks/resolved/` with the same resolution annotation (each file gets its own appended section).

8. **`factory resolve` commits the state transition to git** with a message that includes the task name and reason.

### Pipeline status integration

9. **`factory status` shows `tasks/resolved/` in its pipeline display**, alongside the other task directories.

## Interface Boundaries

### Directories

| Directory | Role | State |
|-----------|------|-------|
| `tasks/failed/` | Open failures needing attention | Active |
| `tasks/resolved/` | Addressed failures (historical record) | Terminal |

### CLI: `factory resolve`

```
factory resolve {task-name} --reason "explanation of how this was resolved"

Arguments:
  task-name    Name of the failed task (filename without .md extension)

Options:
  --reason     Required. How the failure was resolved.

Behavior:
  - Moves tasks/failed/{task-name}.md → tasks/resolved/{task-name}.md
  - Moves tasks/failed/{task-name}.v*.md → tasks/resolved/{task-name}.v*.md
  - Appends ## Resolution section to each moved file
  - Commits to git

Exit codes:
  0  Task resolved successfully
  1  No failure report found in tasks/failed/ for {task-name}
```

### Automatic resolution hook

The function `resolve_completed_failures(workspace)` runs in the post-execution block after Verifier execution, after the task review cleanup and before failure learning extraction. Ordering:

1. Spec pipeline cleanup (every agent)
2. Task review cleanup (every agent)
3. Failure resolution (verifier only)
4. Failure learning extraction (verifier only)

Failure learning extraction runs after resolution so it only processes files still in `tasks/failed/` — i.e., unresolved failures. Resolved failures have already had their learnings extracted on a prior cycle (the learning was extracted when the failure report first appeared, before resolution).

### Resolution annotation format

```markdown
## Resolution
- resolved_by: rebuild | manual
- resolved_at: 2026-02-24T13:00:00
- verified_task: tasks/verified/{task-name}.md    # only for rebuild
- reason: {text}                                   # only for manual
```

The annotation is appended to the end of the existing file content. It does not modify existing sections.

## Constraints

- **`factory resolve` requires `--reason`.** No silent closures. Every manual resolution must explain what happened. The command prints an error and exits non-zero if `--reason` is omitted.
- **Resolution is one-directional.** Files in `tasks/resolved/` are never moved back to `tasks/failed/`. If a resolved task needs to fail again, a new failure report is written by Verifier in the normal course of verification.
- **Automatic resolution only fires after Verifier execution.** It does not run after other agents. This prevents premature resolution — a task should only be considered resolved when Verifier has confirmed the rebuild passes.
- **The resolution pass is idempotent.** If a versioned failure report already exists in `tasks/resolved/`, it is not moved again (the source no longer exists in `tasks/failed/`).
- **Failure learning extraction is unaffected.** Learnings are extracted based on the presence of `## Generalizable Learning` sections in `tasks/failed/` files. The resolution pass runs before learning extraction in the post-execution sequence, but learning extraction uses a deduplication check (`existing_learning_names`) that prevents re-extraction. Learnings extracted on prior cycles (before resolution) persist in `learnings/failures/`.

## Out of Scope

- **Retention policies for `tasks/resolved/`.** The directory grows indefinitely. Cleanup is a human or operator concern.
- **Reviewer agent changes.** The reviewer already scans `tasks/failed/` for patterns. Once resolved failures move to `tasks/resolved/`, the reviewer naturally stops seeing them. No reviewer code changes needed.
- **Changes to `agents.yaml` or access control.** The runtime handles resolution with full filesystem access. Agent access profiles are unchanged.
- **Automatic detection of which resolution path to use.** The human decides between `factory rebuild` and `factory resolve`. The runtime provides both mechanisms.

## Verification Criteria

- After `factory rebuild seed-skill-gaps` succeeds through the full pipeline (Builder rebuilds, Verifier passes), the versioned failure report `tasks/failed/seed-skill-gaps.v1.md` no longer exists in `tasks/failed/` and instead exists in `tasks/resolved/seed-skill-gaps.v1.md` with a `## Resolution` section indicating `resolved_by: rebuild`.
- Running `factory resolve self-review-loop --reason "human added reviewer agent to agents.yaml"` moves `tasks/failed/self-review-loop.md` to `tasks/resolved/self-review-loop.md` with the provided reason in the `## Resolution` section.
- Running `factory resolve` without `--reason` prints an error and does not modify the filesystem.
- Running `factory resolve nonexistent-task --reason "test"` prints an error naming the missing file and exits non-zero.
- `factory status` shows `tasks/resolved/` with its item count.
- After the resolution pass, `tasks/failed/` contains only genuinely unresolved failures.
- `factory init` creates the `tasks/resolved/` directory.
