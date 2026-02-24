# Outcome

Done. The `pipeline-next-step` spec has been implemented and moved to review.

**What was built:** `PIPELINE_DOWNSTREAM` dict and `print_pipeline_next` in `runtime/factory_runtime/cli.py`.

- Pipeline topology encoded as a single module-level dict — no conditionals scattered through logic
- After each successful `factory run <agent>` (including NO_REPLY), prints downstream directories that have work, with yellow counts and bold actionable commands, or a dim idle message if nothing is waiting
- Exception path untouched — `sys.exit(1)` fires before `print_pipeline_next` is ever reached
- Informational-only entries (researcher → `tasks/research-done/`, verifier → `tasks/failed/` / `tasks/verified/`) print count but no `— next:` suffix

**State transitions completed:** spec archived → `specs/archive/pipeline-next-step.md`, review task at `tasks/review/pipeline-next-step.md`.
