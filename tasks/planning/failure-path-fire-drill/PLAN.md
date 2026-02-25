# Plan: failure-path-fire-drill

spec: specs/ready/failure-path-fire-drill.md
planned_at: 2026-02-26T07:15:36

## Summary

Adds `factory fire-drill` — a synchronous CLI command that exercises the four
unvalidated failure-workflow functions (`extract_failure_learnings`,
`rebuild_task`, `resolve_completed_failures`) with synthetic data, verifies
each produces correct output, and cleans up all artifacts before exiting.

All implementation is in `runtime/factory_runtime/cli.py`.  No new files,
modules, or dependencies required.  The spec's §7 ambiguities are
pre-resolved; no decision gates needed.

---

## Tasks

### Task 1 — Implement `fire_drill()` function

**File:** `runtime/factory_runtime/cli.py`
**Insert after:** `rebuild_task()` (currently ends at line ~1420), before
`_CATEGORY_DISPLAY_ORDER` (line ~1422).

**Signature:**
```python
def fire_drill(workspace: Path, force: bool) -> tuple[int, list[str]]:
```

Returns `(exit_code, report_lines)` where `exit_code` is 0 (PASS) or 1 (FAIL),
and `report_lines` is the step-by-step display list.

**Logic (in order):**

#### Pre-flight guard (runs before try/finally)

Scan these dirs for any filename containing `fire-drill-canary`:
- `tasks/failed/`
- `tasks/resolved/`
- `tasks/verified/`
- `specs/ready/`
- `specs/archive/`
- `learnings/failures/`

If stale files found:
- Without `force`: return `(1, [warning lines listing each stale file])`
- With `force`: remove each stale file via `os.remove()`, continue

#### Synthetic artifact content

**Failure report** (`tasks/failed/fire-drill-canary.md`) — written in Step 1:
```
# Verification Report: fire-drill-canary

spec: specs/archive/fire-drill-canary.md
reviewed_at: {datetime.now().isoformat(timespec='seconds')}
verdict: NOT SATISFIED (4/10)

## Summary
This is a synthetic failure report created by `factory fire-drill` to validate the failure workflow infrastructure.

## Artifact-by-Artifact Assessment
- **Synthetic criterion**: The spec required a working implementation. The fire-drill canary has no implementation — it is a synthetic validation artifact.

## Satisfaction Score: 4/10
Score chosen to be clearly below the passing threshold while exercising the score extraction regex in `rebuild_task()`.

## Path to Resolution
Implement the missing functionality described in the spec. This section exists to validate that `rebuild_task()` correctly extracts it into the rebuild brief.

## Generalizable Learning
Untested infrastructure pathways represent latent risk. Failure workflows should be validated before they are needed in production, not after the first real failure reveals gaps in the processing chain.
```

**Archived spec** (`specs/archive/fire-drill-canary.md`) — written in Step 3:
```
# fire-drill-canary

## Overview
This is a synthetic spec stub created by `factory fire-drill` to satisfy
the prerequisite check in `rebuild_task()`. It is a transient validation
artifact and will be removed at the end of the fire drill.
```

**Verified report** (`tasks/verified/fire-drill-canary.md`) — written in Step 5:
```
# Verification Report: fire-drill-canary (rebuilt)

verdict: SATISFIED (10/10)
reviewed_at: {datetime.now().isoformat(timespec='seconds')}

## Summary
Synthetic verification pass created by `factory fire-drill` to trigger
`resolve_completed_failures()`.
```

#### try/finally structure

```
step_results = []   # list of (passed: bool, label: str, detail: str | None)
failed_at = None    # step number (1-5) if a step fails

try:
    # Step 1 — write failure report
    # Step 2 — call extract_failure_learnings(), check learnings/failures/
    # Step 3 — write archived spec
    # Step 4 — call rebuild_task(), verify 3 artifacts
    # Step 5 — write verified report, call resolve_completed_failures(), verify move
finally:
    # Step 6 — cleanup (os.remove each artifact if exists)
```

Each step: if it fails, record failure, set `failed_at`, break out of the
try block (do not attempt subsequent steps). Steps after `failed_at` are
recorded as `— Skipped`.

#### Step 2 detail

After calling `extract_failure_learnings(workspace)`, glob
`learnings/failures/` for any filename containing `fire-drill-canary`.
If none found → fail with message:
`"extract_failure_learnings did not produce expected output"`

#### Step 4 detail

Call `rebuild_task(workspace, "fire-drill-canary")`.
- If return code ≠ 0 → fail: `f"rebuild_task returned exit code {code}: {msg}"`
- Check each artifact exists; collect missing names:
  - `tasks/failed/fire-drill-canary.v1.md`
  - `specs/ready/fire-drill-canary.md`
  - `specs/ready/fire-drill-canary.rebuild.md`
- If any missing → fail: `f"Missing artifacts: {', '.join(missing)}"`

#### Step 5 detail

Write `tasks/verified/fire-drill-canary.md`, call
`resolve_completed_failures(workspace)`, then check:
- `tasks/failed/fire-drill-canary.v1.md` must NOT exist
- `tasks/resolved/fire-drill-canary.v1.md` must exist
- Content of resolved file must contain `## Resolution`

If any check fails → fail with description of violation.

#### Cleanup (finally block)

Remove each path via `os.remove()` if it exists (silently skip missing):
```
tasks/resolved/fire-drill-canary.v1.md
learnings/failures/*fire-drill-canary*   (glob)
specs/archive/fire-drill-canary.md
specs/ready/fire-drill-canary.md
specs/ready/fire-drill-canary.rebuild.md
tasks/verified/fire-drill-canary.md
tasks/failed/fire-drill-canary.md
tasks/failed/fire-drill-canary.v1.md
```

For the glob, use `list(workspace.glob("learnings/failures/*fire-drill-canary*"))`.

#### Report format

Build report lines from `step_results`.  Success:
```
Fire drill: failure workflow validation
  ✓ Step 1: Synthetic failure report created
  ✓ Step 2: Learning extraction verified
  ✓ Step 3: Synthetic spec archived
  ✓ Step 4: Rebuild verified (3 artifacts)
  ✓ Step 5: Auto-resolution verified
  ✓ Step 6: Cleanup complete

Result: PASS — all failure workflow functions validated
```

Failure (example at step 2):
```
Fire drill: failure workflow validation
  ✓ Step 1: Synthetic failure report created
  ✗ Step 2: Learning extraction — extract_failure_learnings did not produce expected output
  — Steps 3-5: Skipped (prior failure)
  ✓ Step 6: Cleanup complete

Result: FAIL — failure at step 2
```

Return `(0, report_lines)` on PASS, `(1, report_lines)` on FAIL.

**Dependencies:** None (calls only existing functions)
**Expected output:** `fire_drill()` function in `cli.py`, ~90-130 lines

---

### Task 2 — Wire `fire-drill` CLI command

**File:** `runtime/factory_runtime/cli.py`
**Insert after:** `rebuild` command handler (currently ends at line ~3925),
before `parse_decision_entries` (line ~3927).

**Implementation:**
```python
@main.command(name="fire-drill", short_help="Validate failure workflow with synthetic data")
@click.option("--force", is_flag=True, default=False,
              help="Remove stale fire-drill-canary artifacts before running.")
def fire_drill_cmd(force: bool) -> None:
    """Exercise the failure workflow functions with synthetic data.

    Creates a synthetic failure report, runs extract_failure_learnings(),
    rebuild_task(), and resolve_completed_failures() in sequence, verifies
    each produces correct output, then cleans up all synthetic artifacts.

    \b
    Exit codes:
      0  All steps passed (PASS)
      1  A step failed, or stale artifacts detected without --force
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    exit_code, report_lines = fire_drill(config.workspace, force)
    for line in report_lines:
        console.print(line)
    sys.exit(exit_code)
```

**Update `_CMD_CATEGORIES`** (line ~4884):
Add `"fire-drill"` to the `"operate"` list alongside `"rebuild"` and
`"resolve"`:
```python
"operate": [
    "status", "start", "run", "advance", "decide",
    "needs", "rebuild", "resolve", "fire-drill", "reflect",
],
```

**Dependencies:** Task 1
**Expected output:** `fire-drill` command registered, appears in `factory --help`

---

### Task 3 — Verify end-to-end

Run the command against the live factory workspace:
```
factory fire-drill
```

Expected:
- Prints 6-step report, all ✓
- Exits 0
- No `fire-drill-canary` files remain anywhere under the workspace

Then verify the stale-artifact guard:
```
# Manually create a stale file
touch tasks/failed/fire-drill-canary.md
factory fire-drill       # must exit 1 with warning
factory fire-drill --force  # must exit 0, remove stale file, run clean
```

**Dependencies:** Task 2
**Expected output:** All verification criteria from spec §Verification Criteria pass

---

## Checkpoint Declarations

None. All §7 ambiguities are pre-resolved in the spec. No reversibility-low
or governance-impact decisions remain. Implementation is fully autonomous.

---

## Expected Outputs Summary

| Task | Output |
|------|--------|
| Task 1 | `fire_drill()` function in `cli.py`, ~100 lines |
| Task 2 | `fire-drill` Click command + `_CMD_CATEGORIES` update |
| Task 3 | `factory fire-drill` exits 0 on clean workspace; stale-artifact guard exits 1; `--force` path exits 0 |

---

## Implementation Notes

- `rebuild_task()` is a pure file function — it does not commit to git. The
  fire drill calling it directly (not the `rebuild` CLI command) avoids git
  side effects. ✓
- `resolve_completed_failures()` scans ALL files in `tasks/verified/`. If
  other verified tasks happen to have corresponding failed reports (unlikely
  in practice), they will also be resolved. Accepted per spec constraints.
- `os.remove()` must be used throughout (not shell `rm`) per the known
  interactive alias on this system.
- No WhatsApp notification, no post-execution GC passes. `fire-drill` is a
  direct CLI command, not an agent run.
- The `fire_drill()` function name differs from the Click command name
  (`fire-drill`). The Click entrypoint function is named `fire_drill_cmd` to
  avoid shadowing the internal function.
