---
name: satisfaction-scoring
description: The probabilistic satisfaction metric. Not pass/fail — a judgment about the fraction of users who would be satisfied with this output.
---

## The Metric

The satisfaction score answers this question:

> "Of a population of users who wanted what the spec describes, what fraction
> would be satisfied with this output?"

Express as N/10. A score of 7/10 means roughly 70% of users with that intent
would find the output satisfactory.

This is NOT:
- A code quality score
- A completeness checklist
- A binary pass/fail

It IS:
- A judgment about fitness for purpose
- Calibrated against the spec's stated intent, not your ideal implementation
- A signal about whether the human who wrote the spec would be satisfied

## Scoring Guidelines

**9-10/10** — All verification criteria satisfied. Behaviors match spec exactly.
No undescribed behaviors that would surprise or confuse users.

**7-8/10** — Core behavior correct. One or two minor gaps that most users would
not encounter or would work around easily.

**5-6/10** — Core behavior partially correct. Missing behaviors that a meaningful
fraction of users would need. A determined user could still accomplish the goal.

**3-4/10** — Key requirements not met. The output addresses the problem space but
fails on important criteria.

**1-2/10** — Fundamental misalignment with the spec. The artifact does not do
what was asked.

## Required Reasoning

Always accompany the score with:
- Which criteria were fully satisfied
- Which criteria were partially satisfied or missed
- Why you placed the score where you did rather than one point higher or lower

"I scored this 6/10 rather than 7/10 because the error handling for empty inputs
crashes rather than printing a usage message, which the spec explicitly requires."

## Threshold

A score of 8/10 or higher moves to `tasks/verified/`.
A score of 7/10 or below moves to `tasks/failed/` with a full failure report.
