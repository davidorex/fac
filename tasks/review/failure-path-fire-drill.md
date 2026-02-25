# Build Complete: failure-path-fire-drill

spec: specs/archive/failure-path-fire-drill.md
built_at: 2026-02-26T07:19:08

## Deliverables

### `fire_drill()` function — `runtime/factory_runtime/cli.py`

Inserted after `rebuild_task()`, before `_CATEGORY_DISPLAY_ORDER`. ~165 lines.

- Pre-flight scan of six canary-named directories; exits 1 with listing on stale artifacts, or removes them with `--force`
- 5 sequential steps guarded by `if failed_at is None:`; each step wrapped in try/except to record failure detail without propagating
- `finally` block removes all synthetic artifacts via `os.remove()` and records Step 6 result
- Report builder inserts skipped-steps notice before cleanup line when `failed_at < 5`
- Returns `(0, report_lines)` on PASS, `(1, report_lines)` on FAIL

### `fire_drill_cmd` Click command — `runtime/factory_runtime/cli.py`

Inserted after `rebuild` command handler, before `parse_decision_entries()`. Named `fire-drill` in the CLI.

### `_CMD_CATEGORIES` update

`"fire-drill"` added to `"operate"` list alongside `"rebuild"` and `"resolve"`.

## Verification Results

All spec §Verification Criteria confirmed against live workspace:

| Criterion | Result |
|---|---|
| `factory fire-drill` on clean workspace prints 6-step report, exits 0 | PASS |
| No `fire-drill-canary` files remain after exit 0 | PASS |
| Stale canary artifact → exits 1 with warning listing | PASS |
| `--force` with stale artifact → removes it, exits 0 | PASS |
| Step 2 passes (report format compatible with extraction regex) | PASS |
| Cleanup runs in `finally` regardless of outcome | PASS (structurally guaranteed) |
