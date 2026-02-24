# Verified: pipeline-next-step

spec: specs/archive/pipeline-next-step.md
verified_at: 2026-02-24T10:39Z
verdict: PASS

## Verification Results

All 6 spec verification criteria satisfied:

1. **spec + specs/ready/ populated → shows directory and `factory run builder`** — PASS
   `PIPELINE_DOWNSTREAM["spec"]` maps to `("specs/ready", "factory run builder")`. Loop prints matching line.

2. **builder + tasks/review/ empty → idle message** — PASS
   Single downstream entry has no non-dotfile items → active list empty → idle message printed.

3. **spec + both specs/ready/ and tasks/research/ populated → both shown** — PASS
   Both entries in downstream list; loop iterates all, printing each with items.

4. **librarian → idle message** — PASS
   `PIPELINE_DOWNSTREAM["librarian"]` is `[]` → active always empty → idle message.

5. **Agent exception → no next-step block** — PASS
   `print_pipeline_next` is inside `try` block after `run_agent()`. Exception bypasses via `except` + `sys.exit(1)`.

6. **Pipeline graph as single data structure** — PASS
   `PIPELINE_DOWNSTREAM` is a module-level dict. `print_pipeline_next` iterates generically. No scattered conditionals.

## Additional Checks

- NO_REPLY path still calls `print_pipeline_next` (call is after the if/else branch) — PASS
- Pipeline graph entries match spec table for all 8 agents — PASS
- Output format matches spec template exactly (em-dash, informational-only variant) — PASS
- Rich styling: `[bold]` command, `[yellow]` count, `[dim]` idle — PASS
- Counting excludes dotfiles, consistent with existing `status()` logic — PASS
- No API calls, no file content reads, no changes to `status` command — PASS
- Call site is after run-log line as spec requires — PASS

## Files Reviewed

- `runtime/factory_runtime/cli.py` — all changes verified against spec

No holdout scenarios existed for this task.
