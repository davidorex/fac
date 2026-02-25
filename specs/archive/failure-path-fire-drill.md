# failure-path-fire-drill

## Overview

All three factory verifications to date have passed (scores 10, 9, 9). The failure workflow — Verifier's NOT SATISFIED report format, the runtime's Generalizable Learning extraction (`extract_failure_learnings()`), the rebuild path (`factory rebuild` / `rebuild_task()`), and the auto-resolution lifecycle (`resolve_completed_failures()`) — has never executed. These four runtime functions and two CLI commands have no real-world validation.

This spec adds a `factory fire-drill` command that programmatically exercises the failure workflow functions with synthetic data, verifies each function produces correct output, cleans up all synthetic artifacts, and reports results. The factory gets a repeatable, deterministic validation mechanism for its failure infrastructure.

## Behavioral Requirements

### Command: `factory fire-drill`

1. **When the operator runs `factory fire-drill`**, the runtime executes a sequential validation of the failure workflow functions using synthetic data. Each step depends on the prior step's output. If any step fails, the command halts, cleans up artifacts created so far, and reports the failure point.

2. **Step 1: Create synthetic failure report.** The runtime writes `tasks/failed/fire-drill-canary.md` containing a valid failure report per the verification-protocol format:
   - Header with `spec: specs/archive/fire-drill-canary.md`, `reviewed_at:` (current ISO timestamp), `verdict: NOT SATISFIED (4/10)`
   - All five required sections: Summary, Artifact-by-Artifact Assessment, Satisfaction Score (4/10), Path to Resolution, Generalizable Learning
   - The Generalizable Learning section contains: "Untested infrastructure pathways represent latent risk. Failure workflows should be validated before they are needed in production, not after the first real failure reveals gaps in the processing chain."

3. **Step 2: Validate learning extraction.** The runtime calls `extract_failure_learnings(workspace)` and verifies that a file matching `*fire-drill-canary*` appeared in `learnings/failures/`. If the file does not appear, the step fails with: "extract_failure_learnings did not produce expected output."

4. **Step 3: Create synthetic archived spec.** The runtime writes `specs/archive/fire-drill-canary.md` — a minimal spec stub containing an Overview section and a note that this is a synthetic fire-drill artifact. This file must exist before `rebuild_task()` can run.

5. **Step 4: Validate rebuild.** The runtime calls `rebuild_task(workspace, "fire-drill-canary")` and verifies:
   - Return code is 0
   - `tasks/failed/fire-drill-canary.v1.md` exists (versioned failure report)
   - `specs/ready/fire-drill-canary.md` exists (copied spec)
   - `specs/ready/fire-drill-canary.rebuild.md` exists (rebuild brief containing extracted Path to Resolution)
   If any artifact is missing, the step fails naming the missing file(s).

6. **Step 5: Validate auto-resolution.** The runtime writes `tasks/verified/fire-drill-canary.md` (a minimal synthetic verification pass report), then calls `resolve_completed_failures(workspace)` and verifies:
   - `tasks/failed/fire-drill-canary.v1.md` no longer exists
   - `tasks/resolved/fire-drill-canary.v1.md` exists
   - The resolved file contains a `## Resolution` section with `resolved_by: rebuild`
   If any check fails, the step fails describing the violation.

7. **Step 6: Cleanup.** The runtime removes all synthetic artifacts created during the drill:
   - `tasks/resolved/fire-drill-canary.v1.md`
   - All files matching `learnings/failures/*fire-drill-canary*`
   - `specs/archive/fire-drill-canary.md`
   - `specs/ready/fire-drill-canary.md`
   - `specs/ready/fire-drill-canary.rebuild.md`
   - `tasks/verified/fire-drill-canary.md`
   - `tasks/failed/fire-drill-canary.md`
   - `tasks/failed/fire-drill-canary.v1.md`
   Each path is checked for existence before removal; missing files are silently skipped (some are expected to have been consumed by prior steps). Cleanup runs in a `finally` block so it executes even if a step fails.

8. **Step 7: Report.** The runtime prints a step-by-step report to stdout. On success:
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
   On failure:
   ```
   Fire drill: failure workflow validation
     ✓ Step 1: Synthetic failure report created
     ✗ Step 2: Learning extraction — extract_failure_learnings did not produce expected output
     — Steps 3-5: Skipped (prior failure)
     ✓ Step 6: Cleanup complete

   Result: FAIL — failure at step 2
   ```

9. **Exit code.** `factory fire-drill` exits 0 on PASS, exits 1 on FAIL.

### Guard: pre-existing canary artifacts

10. **Before starting**, the command checks whether any file with `fire-drill-canary` in its name exists in `tasks/failed/`, `tasks/resolved/`, `tasks/verified/`, `specs/ready/`, `specs/archive/`, or `learnings/failures/`. If any exist (from a prior interrupted run), the command prints a warning listing the stale files and exits 1 without running. The `--force` flag removes stale canary files before starting the drill.

## Interface Boundaries

### CLI

```
factory fire-drill [--force]

Options:
  --force    Remove any stale fire-drill-canary artifacts before running

Exit codes:
  0  All steps passed
  1  A step failed, or stale artifacts detected without --force
```

### Synthetic artifact naming

All synthetic files use the stem `fire-drill-canary`. This name is unambiguously synthetic and does not collide with any real spec or task name.

### Function dependencies

The fire drill calls these existing functions in sequence:
1. `extract_failure_learnings(workspace)` — from cli.py
2. `rebuild_task(workspace, "fire-drill-canary")` — from cli.py
3. `resolve_completed_failures(workspace)` — from cli.py

No new runtime functions are created for the individual validation steps. The fire drill is a single function (`fire_drill(workspace, force)`) in cli.py that orchestrates calls to existing functions and asserts their outputs.

### Synthetic failure report template

The failure report written in Step 1 must match this structure exactly:

```markdown
# Verification Report: fire-drill-canary

spec: specs/archive/fire-drill-canary.md
reviewed_at: {current ISO timestamp}
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

## Constraints

- The fire drill must not trigger WhatsApp notifications. It is not an agent run — it is a direct CLI command like `factory status` or `factory needs`.
- The fire drill must not trigger post-execution GC passes. Cleanup is handled by the fire drill's own `finally` block.
- File removal uses `os.remove()` (not shell `rm`) per the system's known `rm` interactive alias.
- The fire drill does not commit to git. It creates and removes transient files within a single command invocation. No state transition occurs that warrants a commit.
- The fire drill completes in a single synchronous invocation — no background processes, no agent dispatch.

## Out of Scope

- Validating Verifier's behavior when writing a failure report. The fire drill validates the runtime functions that *process* failure reports, not the agent that *writes* them. Verifier's failure-writing behavior is governed by the verification-protocol and failure-reporting skills.
- Validating `factory resolve` (manual resolution via `resolve_task()`). The fire drill covers the automated path (`resolve_completed_failures`). Manual resolution is a simpler code path with fewer moving parts.
- Persistent calibration artifacts. The fire drill cleans up after itself. The validation is the deliverable, not the data. The synthetic failure report template is visible in the source code for reference purposes.
- Concurrency guards. The fire drill is a short-lived synchronous operation. The theoretical risk of `factory start` dispatching canary files mid-drill is accepted as a known limitation (documented in constraints), not mitigated with locking.

## Verification Criteria

- Running `factory fire-drill` on the current factory (which has no failures in `tasks/failed/`) prints a 6-step report and exits 0.
- After `factory fire-drill` exits 0, no files containing `fire-drill-canary` in their name exist anywhere under the factory workspace.
- Running `factory fire-drill` when stale canary artifacts exist exits 1 with a warning listing the stale files.
- Running `factory fire-drill --force` when stale canary artifacts exist removes them and proceeds with the drill, exiting 0 if all steps pass.
- The synthetic failure report written in Step 1 is parseable by `extract_failure_learnings()` — Step 2 passes, confirming the report format and the extraction regex are compatible.
- If `rebuild_task()` fails (e.g., returns a non-zero exit code), Step 4 reports the failure and the command exits 1 after cleanup.

## Ambiguities

### 7.1 Naming convention for the canary task
- reversibility: high
- impact: cosmetic
- status: auto-resolved

**Options:**
- **(a)** `fire-drill-canary` — clearly synthetic, unambiguous
- **(b)** `_fire-drill` — underscore prefix convention for internal artifacts
- **(c)** `fire-drill-{timestamp}` — unique per run

**Resolution:** Chose (a). Fixed name is simplest and cleanup is deterministic. Timestamp-based naming complicates cleanup glob patterns. Underscore prefix has no established convention in the factory. The stale-artifact guard handles the collision case (interrupted prior run).

### 7.2 Cleanup vs persistence of artifacts
- reversibility: high
- impact: implementation
- status: auto-resolved

**Options:**
- **(a)** Clean up all artifacts after validation — fire drill leaves no trace
- **(b)** Persist artifacts as calibration data marked with `source: fire-drill`
- **(c)** Clean up by default, `--keep` flag to persist

**Resolution:** Chose (a). The intent's concern about "no calibration data" is addressed by the fire drill validating that the infrastructure works correctly — the synthetic failure report template is visible in source code for anyone who needs a format reference. Mixing synthetic artifacts with real pipeline data would require filtering logic in `factory status`, reviewer pattern scanning, and dispatch. Clean validation is the simpler, lower-risk path.
