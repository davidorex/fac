# Failure Learning: seed-skill-gaps

**Class of failure**: Builder produced content that is individually high-quality but systematically violates a dimensional constraint stated in the spec. 11 of 14 items exceeded the ceiling, suggesting the constraint was deprioritized relative to content quality during implementation.

**Why it occurred**: The spec's line limit (15-40 lines) and its guidance that skills should be "behavioral guidance, not tutorials" create tension when the blueprint's source descriptions are detailed. Builder appears to have optimized for faithfulness and completeness over the dimensional constraint, treating the line limit as a soft target rather than a hard boundary.

**Preventive recommendation**: When a spec includes both a content-quality constraint and a dimensional constraint, treat the dimensional constraint as a hard gate. Write to the ceiling first, then evaluate whether the content is sufficient. If the content cannot be meaningfully expressed within the constraint, flag this as a spec tension in builder notes rather than silently exceeding the limit.

## Source
- Failure report: tasks/failed/seed-skill-gaps.md
- Spec: specs/archive/seed-skill-gaps.md
- Extracted by: runtime (post-verifier execution)
