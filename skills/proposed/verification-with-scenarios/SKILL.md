---
name: verification-with-scenarios
description: How to integrate scenario evaluation into verification reports.
for: verifier
---

## Scenario Evaluation Section

Every verification report includes a `## Scenario Evaluation` section placed
after the spec-matching section.

## With Scenarios Present

For each scenario file found in `scenarios/{project}/` (excluding `_template.md`
and `satisfaction.md`):

1. State the scenario title.
2. Describe how the implementation handles it.
3. Judge whether the scenario is satisfied.

Failed scenarios are described with the same specificity as failed spec
requirements — state exactly what the implementation does and what it should do.

## Without Scenarios

When no scenarios exist for the project, include the section with:

> No scenario holdouts found for this project.

## Scoring

Scenario evaluation contributes to but does not solely determine the satisfaction
score. A strong spec match with poor scenario coverage is still a concern worth
documenting in the report.

## Meta-Scenario

Evaluate factory infrastructure tasks directionally against
`scenarios/meta/factory-itself.md`: does this change move the factory closer to
or further from the meta-scenario? Document the reasoning. Do not apply pass/fail.
