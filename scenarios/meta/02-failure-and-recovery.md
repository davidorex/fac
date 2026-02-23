# Scenario 2: The Failure-and-Recovery Loop

**Title:** Builder fails, Verifier catches it, Builder fixes it

**Story:** Builder implements a project but misses an edge case from the spec. Verifier catches it and writes a failure report. Builder reads the report, fixes the issue, and resubmits.

**Expected trajectory:**

After Builder submits work to `tasks/review/`, Verifier finds that the spec says "when the output directory doesn't exist, create it" but Builder's implementation raises a FileNotFoundError instead. Verifier writes a failure report to `tasks/failed/` that includes: what the spec says, what the code does, and a suggested fix.

Builder picks up the failure on its next heartbeat, reads the report, fixes the code, re-runs tests, and moves the task back to `tasks/review/`. Verifier re-evaluates and this time approves.

**Satisfaction criteria:** The failure report is specific enough that Builder doesn't need to re-read the entire spec. The fix addresses exactly what was reported. The round-trip takes two cycles, not five.
