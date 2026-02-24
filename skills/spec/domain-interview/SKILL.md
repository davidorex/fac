---
name: domain-interview
description: How to interview the human to extract what they actually want. What questions to ask and when to stop asking.
---

## When to Interview

Before writing an NLSpec for anything non-trivial, interview the human if:
- The intent is ambiguous about key behaviors (not just implementation details)
- The scope could be interpreted narrowly or broadly with materially different outcomes
- The domain is unfamiliar and you lack enough context to make reasonable choices

Do NOT interview about implementation details — make a reasonable choice and flag it in the spec's constraints section.

## What to Ask

**Scope boundaries** — what is explicitly in and out of scope
- "Should this handle X, or is that a future concern?"
**Success criteria** — what does "done" look like for the human
- "How would you know this is working correctly?"
- "What would make this version a success even if Z isn't done?"

**Constraints** — real constraints vs. preferences
- "Is [technology choice] required, or do you have flexibility?"
- "Are there existing systems this must integrate with?"

## When to Stop Asking

Stop when you can answer this question confidently:
> "If I write a spec now and Builder implements it, would the human be satisfied?"

Indicators you can stop:
- You can state the behavioral requirements without hedging
- You know what's in scope and what's deferred
- You know the success criteria

Do not ask about implementation decisions that belong to Builder.
Do not ask about things you can reasonably default — pick a choice and note it.

## Conducting the Interview

- Ask at most 3-5 questions at a time — large question lists get incomplete answers
- Prefer concrete, binary questions over open-ended ones for scope decisions
- After each round, restate your updated understanding before asking more
