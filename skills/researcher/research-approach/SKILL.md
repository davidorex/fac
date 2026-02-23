---
name: research-approach
description: How to research a question and deliver a decision-ready recommendation.
---

## The Sequence

1. Clarify the question. What exactly does the requesting agent need to know?
   Not "research React" but "which React state management approach best fits a real-time collaborative app with optimistic updates?"

2. Identify 2-4 candidate approaches. Never research just one option.

3. For each candidate:
   - Find authoritative sources (official docs, maintained repos, reputable technical writing)
   - Evaluate: maturity, maintenance status, community size, known pitfalls
   - Note trade-offs honestly — there is rarely a clear winner

4. Synthesize into a recommendation brief:
   - The question (restated precisely)
   - The candidates (1-2 paragraphs each)
   - The recommendation (which one and WHY)
   - The trade-off (what you lose by choosing the recommendation)
   - Confidence level (high / medium / low with reasoning)

5. Write the brief to `tasks/research-done/{request-id}.md`

## When to Decompose

Research is the most natural place for subagents. If you have 3 candidate libraries to evaluate, spawn 3 subagents — one per library — and synthesize their findings.

## Source Hierarchy

1. Official documentation (current version)
2. Source code and tests (the actual behavior, not what docs claim)
3. Maintained technical blogs by practitioners
4. Conference talks and technical papers
5. Community forums (useful for gotchas, not for architecture decisions)
6. Your own training knowledge (lowest confidence — always flag as such)

## What a Good Brief Looks Like

Short. Decision-ready. The requesting agent reads it in 2 minutes and knows what to do. If your brief exceeds 500 words, you're writing a report. Save details for a linked appendix file.

## Using the Universe

Check `universe/` before going external. The Attractor specs, context engineering docs, and synthesis may already contain relevant patterns or principles. The factory should build on its own foundations.
