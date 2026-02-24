# Review Task: spec-pipeline-cleanup

spec_archive: specs/archive/spec-pipeline-cleanup.md
built_at: 2026-02-24T11:43:44
built_by: builder

## Deliverables

### 1. `run_spec_pipeline_cleanup(workspace, dry_run)` function in `runtime/factory_runtime/cli.py`

Scans `specs/inbox/`, `specs/drafting/`, `specs/ready/`, `specs/archive/` for
duplicate filenames. Removes upstream copies when a downstream stage already holds
the file. Archive is never touched. Returns log lines describing every deletion.
Idempotent.

### 2. Post-execution hook in the `run` command

After `print_pipeline_next()`, `run_spec_pipeline_cleanup()` is called for every
agent execution. Cleaned files are printed as dim console lines.

### 3. `factory cleanup-specs [--dry-run]` CLI command

Standalone invocable command that calls `run_spec_pipeline_cleanup()`.
`--dry-run` shows what would be cleaned without deleting. Reports "Spec pipeline is clean"
when no stale files exist.

## Implementation Location

`runtime/factory_runtime/cli.py` — all changes in this single file.

## Verification Criteria (from spec)

- After running the Spec agent on an inbox intent, the intent file no longer exists in `specs/inbox/`
- After running the Builder agent on a ready spec, the spec no longer exists in `specs/ready/`
- A spec that exists only in `specs/inbox/` (not yet picked up) is not deleted
- `factory cleanup-specs` removes stale files (currently: pipeline-next-step.md and self-review-loop.md in inbox/drafting)
- `factory cleanup-specs --dry-run` lists what would be cleaned without deleting
