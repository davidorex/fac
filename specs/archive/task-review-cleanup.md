# task-review-cleanup

## Overview

The Verifier writes pass/fail reports to `tasks/verified/` or `tasks/failed/` but does not remove the source file from `tasks/review/`. This creates ambiguous pipeline state — stale files in `tasks/review/` look like unverified work to any agent or human inspecting the pipeline. The `spec-pipeline-cleanup` convention (`specs/archive/spec-pipeline-cleanup.md`) solves the identical problem for the spec pipeline but explicitly scopes out `tasks/`. This spec extends the same cleanup pattern to the task pipeline.

Currently 4 files sit in `tasks/review/` that already have corresponding entries in `tasks/verified/`: `spec-pipeline-cleanup.md`, `failure-learning-convention.md`, `failed-task-rebuild-convention.md`, and `seed-skill-gaps.md`. This will recur on every future verification cycle.

## Behavioral Requirements

1. **When the factory runtime finishes executing any agent**, it runs a task review cleanup pass that checks for files in `tasks/review/` that also exist in `tasks/verified/` or `tasks/failed/`. If a file with the same name exists in either downstream directory, the `tasks/review/` copy is stale and is removed.

2. **When the cleanup pass deletes a file**, it logs the action: `"Cleaned stale task: tasks/review/foo.md (exists in tasks/verified/)"` (or `tasks/failed/` as appropriate). If a file exists in both `tasks/verified/` and `tasks/failed/`, the log references whichever downstream directory is checked first (verified before failed — the ordering is cosmetic only; the file is removed either way).

3. **The cleanup pass is also available as a standalone CLI command**: `factory cleanup-tasks`, with a `--dry-run` flag that lists what would be cleaned without deleting.

4. **The cleanup pass runs after the existing spec pipeline cleanup** in the post-execution sequence. The order within post-execution hooks is: spec pipeline cleanup → task review cleanup → failure learning extraction (verifier only). This ordering is for readability of log output only — the passes are independent and could run in any order.

## Interface Boundaries

### Directories involved

- `tasks/review/` — upstream: completed work awaiting verification
- `tasks/verified/` — downstream: Verifier passed the task
- `tasks/failed/` — downstream: Verifier failed the task (active failure slot only — versioned `.v{N}.md` files are not considered matches)

### Matching criterion

Exact filename match. `foo.md` in `tasks/verified/` or `tasks/failed/` causes deletion of `foo.md` in `tasks/review/`. Versioned failure reports (`foo.v1.md`, `foo.v2.md`) in `tasks/failed/` are **not** considered matches for `foo.md` in `tasks/review/` — only the base filename matches.

### CLI interface

```
factory cleanup-tasks            # Run the task review cleanup manually
factory cleanup-tasks --dry-run  # Show what would be cleaned without deleting
```

### Integration point

The function `run_task_review_cleanup(workspace, dry_run=False)` is added to `cli.py` (or a shared module). It is called in the `run` command's post-execution block, after `run_spec_pipeline_cleanup` and before `extract_failure_learnings`. It runs regardless of which agent was executed.

### Function signature

```python
def run_task_review_cleanup(workspace: Path, dry_run: bool = False) -> list[str]:
    """Remove stale files from tasks/review/ that exist in tasks/verified/ or tasks/failed/.

    Returns a list of log lines describing every deletion (or planned deletion when dry_run=True).
    """
```

## Constraints

- The cleanup pass **never deletes files from `tasks/verified/` or `tasks/failed/`**. It only removes upstream copies from `tasks/review/`.
- The cleanup pass **never deletes a file from `tasks/review/` that has no downstream match**. A task in `tasks/review/` with no corresponding file in `tasks/verified/` or `tasks/failed/` is untouched — it's genuinely awaiting verification.
- Versioned failure reports (`*.v{N}.md`) in `tasks/failed/` are **not** treated as matches. Only the active (non-versioned) filename matches. This avoids incorrectly cleaning a task that was rebuilt (versioned failure exists, but current build cycle is still in review).
- The cleanup pass is **idempotent** — running it multiple times produces the same result as running it once.
- Git commits for cleanup deletions are handled by the agent's normal commit behavior, not by the cleanup pass itself.

## Out of Scope

- Cleanup of `tasks/research/` after `tasks/research-done/` is populated. The research lifecycle has different semantics (multiple agents may read research-done, the request may be re-issued) and warrants its own convention if needed.
- Cleanup of `tasks/building/`. Builder manages its own work-in-progress directory.
- Changes to `agents.yaml` or agent access control.
- Changes to the Verifier's behavior. The Verifier continues to write only to `tasks/verified/` or `tasks/failed/`. Cleanup is a runtime concern.

## Verification Criteria

- After running the Verifier on a task in `tasks/review/`, the post-execution cleanup removes that task from `tasks/review/` (because it now exists in `tasks/verified/` or `tasks/failed/`).
- The currently stale files (`spec-pipeline-cleanup.md`, `failure-learning-convention.md`, `failed-task-rebuild-convention.md`, `seed-skill-gaps.md`) in `tasks/review/` are removed by running `factory cleanup-tasks`.
- `factory cleanup-tasks --dry-run` lists the 4 currently stale files without deleting them.
- A task that exists only in `tasks/review/` (not yet verified) is not deleted by the cleanup pass.
- A task that was rebuilt (has `tasks/failed/{name}.v1.md` but no `tasks/failed/{name}.md`) and is currently in `tasks/review/` awaiting re-verification is not deleted by the cleanup pass — the versioned failure report is not treated as a downstream match.
