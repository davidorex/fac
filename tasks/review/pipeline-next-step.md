# Review: pipeline-next-step

spec_archive: specs/archive/pipeline-next-step.md

## What was built

Added `print_pipeline_next` function and `PIPELINE_DOWNSTREAM` data structure to
`runtime/factory_runtime/cli.py`. The function is called inside the `run` command
after the run-log line is printed, on every successful completion (including NO_REPLY),
but not on exception (exception path exits via `sys.exit(1)` before the call).

## Files changed

- `runtime/factory_runtime/cli.py` — added `PIPELINE_DOWNSTREAM` dict, `print_pipeline_next`
  function, and the call site in the `run` command

## Implementation notes

- `PIPELINE_DOWNSTREAM` is a module-level dict mapping agent name to a list of
  `(relative_dir, command_or_None)` tuples. This is the single authoritative data
  structure for pipeline awareness — no logic is scattered across conditionals.
- Items are counted as any entry in the directory whose name does not start with `.`,
  matching the existing `status` command counting logic.
- Output uses rich formatting: yellow for non-zero counts, bold for the command portion,
  dim for the idle message.
- `Optional` imported from `typing` for the type annotation. `from __future__ import
  annotations` was already present.

## Verification criteria (from spec)

1. After `factory run spec` when `specs/ready/` contains a file → output includes
   `specs/ready/` and `factory run builder`
2. After `factory run builder` when `tasks/review/` is empty → output includes idle message
3. After `factory run spec` when both `specs/ready/` and `tasks/research/` contain files
   → both directories appear in output
4. After `factory run librarian` → idle message appears (librarian has no downstream)
5. When agent run errors out → no next-step block appears
6. Pipeline graph is defined as a single data structure, not spread across conditionals
