---
name: source-evaluation
description: How to judge whether information is reliable. Applies a source hierarchy before incorporating any finding into a research brief.
---

## Source Hierarchy

When evaluating information, apply this ordering — prefer higher tiers:

1. **Official documentation** — vendor docs, RFC specs, language references
2. **Primary source code** — the actual library/project, not descriptions of it
3. **Recent authoritative blog posts** — from known maintainers or recognized experts
4. **Stack Overflow / community Q&A** — useful for patterns, check answer date and vote count
5. **LLM training data recall** — treat as a starting point only, not ground truth

When two sources conflict, the higher-tier source wins. When a lower-tier source
contradicts official docs, note the discrepancy rather than silently resolving it.

## Recency Check

- API and library guidance older than 2 years is suspect — check for version drift
- Security guidance must be current — old advisories may describe fixed issues
- Architectural patterns are longer-lived — age alone does not disqualify them
- Always note the date or version of a key source in the research brief

## Maintenance Status

Before recommending a library or tool, check:
- Last release date and commit frequency
- Open issues vs. closed issues ratio
- Whether the README references abandonment or a maintained fork
- Community size (number of contributors, downstream dependents)

An abandoned library may still be the right answer for stable, finished domains.
Flag it explicitly rather than hiding it.

## Red Flags

- Source cites no version and the landscape changes quickly
- Source author has obvious vendor bias for one option
- "Best practice" advice with no rationale — look for the reasoning
- A single source supporting a strong claim — find corroboration
