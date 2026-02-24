# Rebuild Brief: seed-skill-gaps

prior_failure: tasks/failed/seed-skill-gaps.v1.md
prior_score: unknown

## What to Fix
Builder should trim each of the 11 failing skills to ≤40 lines of guidance content. The content is substantively good — the task is editorial compression, not rewriting. Specific approaches:
- Remove worked examples and concrete snippets where the behavioral rule is self-explanatory
- Collapse multi-line bullet lists into denser formulations
- For `spec-spec-patterns` (110 lines): the four skeleton templates cannot fit in 40 lines. Consider referencing a separate template file or providing only one representative skeleton with a note that patterns expand over time
- Several skills are only 5-8 lines over; minor trimming suffices
