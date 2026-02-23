---
name: verification-protocol
description: How to evaluate whether Builder's output satisfies the spec.
---

## The Sequence

1. Read the spec from `specs/ready/`
2. Read Builder's notes from `tasks/review/{task}/builder-notes.md`
3. Read/clone the project from `projects/{project}/`
4. Run the existing tests. Note results.
5. Read the scenario holdouts from `scenarios/{project}/`
6. For each scenario: walk through it against the actual system. Does it behave as described?
7. Score satisfaction: "Of 10 users who wanted what the spec describes, how many would be satisfied?"
8. Write your assessment:
   - Satisfied (≥ 8/10): move to `tasks/verified/`, write `scenarios/{project}/satisfaction.md`
   - Not satisfied: move to `tasks/failed/`, write failure report

## What You're Checking

- Behavioral correctness: does it DO what the spec says?
- Boundary correctness: edges, errors, constraints handled?
- Completeness: anything in the spec NOT implemented?
- Excess: anything implemented NOT in the spec? (Gold-plating is also a failure.)

## What You're NOT Checking

- Code style (unless spec mentions it)
- Performance (unless spec has performance constraints)
- Whether you'd have done it differently

## Satisfaction Scoring

Not pass/fail. A probability: "what fraction of the intended users would be satisfied?"
Include your reasoning. A score of 6/10 with clear reasoning is more useful than 10/10 with none.
