---
name: scenario-evaluation
description: How to evaluate implementation against holdout scenarios. Run each scenario and assess whether the system behaves as expected.
---

## What Scenarios Are

Holdout scenarios in `scenarios/{project-name}/` are end-to-end user stories that
Builder never sees. They describe concrete situations: a user wants to do X, they
invoke the system in way Y, the expected outcome is Z.

Scenarios test whether the system works for real user intent, not just whether it
satisfies the spec's stated criteria. A system can satisfy every spec criterion
and still fail a scenario if the spec missed something.

## How to Evaluate a Scenario

For each scenario file:

1. **Read the scenario completely** before starting evaluation
2. **Identify the setup conditions** — what state is the system in before the scenario begins?
3. **Trace the user actions** — either run them actually (if safe and feasible) or trace them mentally through the code
4. **Compare the outcome** — does the system produce what the scenario expects?
5. **Record your finding** — pass / partial / fail with specific evidence

"Pass" requires the output to match the expected outcome, not just to be close.
"Partial" means the system does something reasonable but not what the scenario expected.
"Fail" means the system does something wrong, crashes, or does nothing.

## When to Run vs. When to Trace

**Run** when the scenario involves CLI invocation with specific inputs and is safe
to execute. **Trace** when running requires external setup or tests an unsafe error
path. Prefer running — tracing introduces your own reasoning errors.

## Recording Results

Write results to `scenarios/{project-name}/satisfaction.md` with one entry per
scenario: scenario name, Result (PASS/PARTIAL/FAIL), and specific evidence observed.
Aggregate results factor into the satisfaction score.
