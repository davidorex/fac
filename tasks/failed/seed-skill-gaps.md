# Verification Report: seed-skill-gaps

spec: specs/archive/seed-skill-gaps.md
reviewed_at: 2026-02-24T12:00
verdict: NOT SATISFIED (5/10)

## Summary

Of the 14 proposed skills, only 3 satisfy all spec criteria. The remaining 11 exceed the spec's explicit 15-40 line content ceiling. All 14 pass on YAML frontmatter validity, behavioral guidance quality, and blueprint faithfulness. The single systemic failure is the line count constraint, which the spec states as a hard constraint: "Content length: 15-40 lines of guidance content (excluding YAML frontmatter). Longer skills are overreaching."

## Artifact-by-Artifact Assessment

| # | Skill | Frontmatter | Lines (limit: 40) | Behavioral | Blueprint Faithful | Result |
|---|-------|:-----------:|:-----------------:|:----------:|:-----------------:|:------:|
| 1 | researcher-source-evaluation | PASS | PASS (37) | PASS | PASS | **PASS** |
| 2 | researcher-recommendation-format | PASS | FAIL (50) | PASS | PASS | FAIL |
| 3 | spec-domain-interview | PASS | FAIL (47) | PASS | PASS | FAIL |
| 4 | spec-spec-patterns | PASS | FAIL (110) | PASS | PASS | FAIL |
| 5 | builder-convergence | PASS | FAIL (48) | PASS | PASS | FAIL |
| 6 | builder-tool-use | PASS | FAIL (46) | PASS | PASS | FAIL |
| 7 | verifier-satisfaction-scoring | PASS | FAIL (52) | PASS | PASS | FAIL |
| 8 | verifier-scenario-evaluation | PASS | FAIL (50) | PASS | PASS | FAIL |
| 9 | verifier-failure-reporting | PASS | FAIL (45) | PASS | PASS | FAIL |
| 10 | librarian-pattern-detection | PASS | FAIL (46) | PASS | PASS | FAIL |
| 11 | librarian-memory-hygiene | PASS | FAIL (49) | PASS | PASS | FAIL |
| 12 | operator-ci-cd | PASS | FAIL (54) | PASS | PASS | FAIL |
| 13 | operator-dependency-management | PASS | PASS (40) | PASS | PASS | **PASS** |
| 14 | operator-monitoring | PASS | PASS (40) | PASS | PASS | **PASS** |

### What passed

- All 14 have valid YAML frontmatter with `name` and `description`
- All 14 are genuine behavioral guidance, not tutorials
- All 14 are faithful to the blueprint descriptions
- No existing skill files were modified (git status clean)
- Naming convention `{agent}-{skill-name}` correctly indicates target directories

### What failed

11 of 14 skills exceed 40 lines of guidance content. The overages range from 5 lines (failure-reporting at 45) to 70 lines (spec-patterns at 110). The spec states this is a hard constraint: "Longer skills are overreaching; shorter skills lack actionable guidance."

The worst offender, `spec-spec-patterns` (110 lines), contains four complete NLSpec skeleton templates. The blueprint describes this as "a growing library of spec templates" — the content is inherently bulky, but the spec ceiling is unambiguous.

## Satisfaction Score: 5/10

The content quality is genuinely good. Every skill accurately captures the blueprint's intent and provides useful behavioral guidance. The failure is purely dimensional — the spec set a 40-line ceiling and 11 of 14 skills break it. A user who cares about content quality would be partially satisfied; a user who cares about spec compliance would not.

## Path to Resolution

Builder should trim each of the 11 failing skills to ≤40 lines of guidance content. The content is substantively good — the task is editorial compression, not rewriting. Specific approaches:
- Remove worked examples and concrete snippets where the behavioral rule is self-explanatory
- Collapse multi-line bullet lists into denser formulations
- For `spec-spec-patterns` (110 lines): the four skeleton templates cannot fit in 40 lines. Consider referencing a separate template file or providing only one representative skeleton with a note that patterns expand over time
- Several skills are only 5-8 lines over; minor trimming suffices

## Generalizable Learning

**Class of failure**: Builder produced content that is individually high-quality but systematically violates a dimensional constraint stated in the spec. 11 of 14 items exceeded the ceiling, suggesting the constraint was deprioritized relative to content quality during implementation.

**Why it occurred**: The spec's line limit (15-40 lines) and its guidance that skills should be "behavioral guidance, not tutorials" create tension when the blueprint's source descriptions are detailed. Builder appears to have optimized for faithfulness and completeness over the dimensional constraint, treating the line limit as a soft target rather than a hard boundary.

**Preventive recommendation**: When a spec includes both a content-quality constraint and a dimensional constraint, treat the dimensional constraint as a hard gate. Write to the ceiling first, then evaluate whether the content is sufficient. If the content cannot be meaningfully expressed within the constraint, flag this as a spec tension in builder notes rather than silently exceeding the limit.
