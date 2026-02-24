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

## What Each Section Must Do

**Question** — Ensures your brief answers what was actually asked. Re-reading
the original request before writing this catches scope drift.

**Options Considered** — Shows your work. The requester may have context you
don't — listing what you considered lets them catch a missed option.

**Recommendation** — Must be specific enough to act on. "Use FastAPI" is
a recommendation. "Consider a Python web framework" is not.

**Trade-offs** — The most important section for avoiding surprise. A
recommendation without trade-offs is an incomplete recommendation.

**Confidence** — Honest calibration. Low confidence on a minor question is
fine. Low confidence on a core architectural choice is a flag to request
deeper research or human input.

## Length

Stay under 500 words for the brief body. If you need to go longer, you have
too many options or too much uncertainty — narrow the question first.
