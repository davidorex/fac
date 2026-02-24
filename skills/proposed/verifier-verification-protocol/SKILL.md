---
name: verification-protocol
description: How Verifier writes failure reports, including the mandatory Generalizable Learning section that the runtime extracts to learnings/failures/.
---

## Verification Flow

When evaluating a task from `tasks/review/`:

1. Read the original spec from `specs/archive/{task-name}.md`
2. Read the implementation artifact(s) referenced in the review task
3. Run or mentally trace through the verification criteria
4. Produce a satisfaction score (see `satisfaction-scoring` skill)

## Failure Report Format

When verdict is NOT SATISFIED, write to `tasks/failed/{task-name}.md`:

```markdown
# Verification Report: {task-name}

spec: specs/archive/{task-name}.md
reviewed_at: {ISO timestamp}
verdict: NOT SATISFIED ({score}/10)

## Summary
{What was evaluated and the overall finding}

## Artifact-by-Artifact Assessment
{For each deliverable in the spec: what was expected, what was found}

## Satisfaction Score: {N}/10
{Reasoning for the score}

## Path to Resolution
{What Builder or a human would need to do to satisfy the spec}

## Generalizable Learning
{REQUIRED — see requirements below}
```

## Generalizable Learning Requirements

This section is **mandatory** in every failure report. The runtime extracts it
to `learnings/failures/` automatically. A missing section causes a runtime warning.

The section must:

- Identify the **class** of failure, not just the instance. Examples:
  - "Specs that require modifying human-only files create unresolvable blockers for agents"
  - "Argparse does not natively reject empty strings — explicit `parser.error()` is needed"
  - "A convention spec with no code artifact still needs explicit verification criteria"
- Explain **why** the failure occurred at the class level
- State **what should be done differently** in future specs or implementations
- NOT restate the Path to Resolution or Summary — it must add new insight

A useful generalizable learning reads like advice to a future agent who will
encounter the same class of situation, not like a description of this specific task.

## Re-Verification

When a task that previously failed appears in `tasks/review/` again:

- Perform a fresh verification against the original spec
- Do not reference or be influenced by the prior failure report
- Write a complete new verification report
- The prior report is preserved in git history — do not append to it
