---
name: satisfaction-scoring
description: The probabilistic satisfaction metric. Not pass/fail — a judgment about the fraction of users who would be satisfied with this output.
---

## The Metric

The satisfaction score answers this question:

> "Of a population of users who wanted what the spec describes, what fraction
> would be satisfied with this output?"

Express as N/10. This is a judgment about fitness for purpose, calibrated against
the spec's stated intent — not a code quality score, completeness checklist, or
binary pass/fail.

## Scoring Guidelines

**9-10/10** — All verification criteria satisfied, no unexpected behaviors.
**7-8/10** — Core behavior correct. Minor gaps most users wouldn't encounter.
**5-6/10** — Core behavior partially correct. Missing behaviors a meaningful fraction needs.
**3-4/10** — Key requirements not met.
**1-2/10** — Fundamental misalignment with the spec.

## Required Reasoning

Always accompany the score with:
- Which criteria were fully satisfied
- Which criteria were partially satisfied or missed
- Why you placed the score where you did rather than one point higher or lower

## Threshold

A score of 8/10 or higher moves to `tasks/verified/`.
A score of 7/10 or below moves to `tasks/failed/` with a full failure report.
