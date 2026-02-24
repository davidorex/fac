---
name: recommendation-format
description: How to deliver research findings as a decision-ready brief. Not a research paper — an actionable answer with trade-offs surfaced.
---

## The Brief Structure

Every research output written to `tasks/research-done/` must follow this structure:

```
## Question
{Restate the question you were asked to answer — one sentence}

## Options Considered
{List the options evaluated, even those you ruled out quickly}

## Recommendation
{One clear recommendation — not "it depends" without a resolution}

## Reasoning
{Why this option over the others — specific, not generic}

## Trade-offs
{What you lose by choosing this recommendation over the alternatives}

## Confidence
{High / Medium / Low — and why}

## Sources
{Key sources with dates or versions}
```

**Trade-offs** — The most important section for avoiding surprise. A recommendation
without trade-offs is an incomplete recommendation.

**Confidence** — Honest calibration. Low confidence on a minor question is fine. Low
confidence on a core architectural choice is a flag to request deeper research or human
input.

## Length

Stay under 500 words. If you need more, the question is too broad — narrow it first.
