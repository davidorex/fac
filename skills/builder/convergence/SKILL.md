---
name: convergence
description: How to know when you're done. Run tests, check the spec. If both pass, stop. If the same issue persists after 3 iterations, write a failure note and stop.
---

## The Convergence Check

After each implementation attempt, run this check in order:

1. **Do the tests pass?**
   - If no tests exist, write the minimum tests that cover the verification criteria
   - If tests fail, iterate
2. **Does the implementation satisfy the spec's Verification Criteria?**
   - Read each criterion literally — not charitably
   - If a criterion is ambiguous, implement the conservative interpretation and flag it
3. **Are there behaviors the code exhibits that the spec does not describe?**
   - Undescribed behaviors are scope creep — remove or flag them

If both (1) and (2) are satisfied, **stop**. Do not add features the spec doesn't mention.

## Iteration Limit

Track the number of times you have attempted to fix the same failing criterion.

- After 2 iterations: note the difficulty in your daily log, consider whether the spec is ambiguous
- After 3 iterations on the same issue: **stop and write a failure note**

A failure note goes to `tasks/review/{task-name}.md` with a `failure: true` flag and
an explanation of what you tried, what the spec requires, and why you could not
converge. Do not write to `tasks/review/` without first writing this note — it is
not Builder's job to silently deliver broken work.

## What "Done" Looks Like

- All verification criteria are satisfied
- Tests cover the verification criteria
- No obvious regressions to other behaviors
- Code is committed to git

Done does not mean:
- The code is beautiful
- Every edge case is handled
- The implementation matches what you would have chosen in a greenfield project

