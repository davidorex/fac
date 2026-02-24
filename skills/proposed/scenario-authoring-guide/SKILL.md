---
name: scenario-authoring-guide
description: When and how to write scenario holdouts for factory verification.
for: human
---

## When to Write Scenarios

Write scenarios BEFORE or ALONGSIDE specs — never after implementation. Scenarios
written after implementation are no longer holdouts; the builder has already seen
the context that shaped them.

## How Many

2–5 scenarios per project. Cover major user paths without becoming a test suite.
More scenarios add cost without adding coverage signal.

## Perspective

Write from the user's perspective, not the developer's. Describe what the user
does and what they observe — not what functions are called or what files change.

## What to Focus On

Focus on the non-obvious: edge cases, error recovery, interaction patterns the
spec might not make explicit. The spec covers the happy path; scenarios stress-test
the assumptions underneath it.

## Holdout Rule

Scenarios MUST NOT be shared with Builder — holdout by design. If Builder sees
scenarios, they become implementation targets rather than independent verification
criteria. The `scenarios/` directory is Builder-inaccessible for this reason.

## Meta-Scenario Use

For factory infrastructure work, evaluate against `scenarios/meta/factory-itself.md`
directionally (does this change move the factory closer to the meta-scenario?),
not as a pass/fail gate.
