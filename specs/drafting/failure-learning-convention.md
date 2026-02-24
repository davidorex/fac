# failure-learning-convention

## Overview

When Verifier fails a task, the failure report captures what went wrong but no generalizable learning is extracted for future reference. The `learnings/failures/` directory is empty despite the factory having experienced at least one verification failure (`self-review-loop`, scored 7/10). Additionally, there is no defined path for re-verifying a failed task after its blocker is resolved — the task sits in `tasks/failed/` indefinitely.

This spec establishes two conventions: (1) every failure report must include a generalizable learning section, which the runtime extracts to `learnings/failures/` automatically, and (2) the re-verification path for resolved failures is documented and supported.

## Behavioral Requirements

### Failure learning extraction

1. **When Verifier writes a failure report to `tasks/failed/{task}.md`**, the failure report must include a `## Generalizable Learning` section containing: the class of problem encountered, why it occurred, and what should be done differently in future specs or implementations. This section must contain insight beyond restating what failed — it must identify the *pattern* so future agents can avoid the same class of failure.

2. **When the factory runtime finishes executing the Verifier agent**, the runtime checks each file in `tasks/failed/` for a `## Generalizable Learning` section. For any failure report containing this section, if no corresponding file exists in `learnings/failures/` (matched by task name), the runtime extracts the section and writes it to `learnings/failures/{YYYY-MM-DD}-{task-name}-verification-failure.md` with the following format:

   ```markdown
   # Failure Learning: {task-name}

   {content of the ## Generalizable Learning section}

   ## Source
   - Failure report: tasks/failed/{task-name}.md
   - Spec: specs/archive/{task-name}.md
   - Extracted by: runtime (post-verifier execution)
   ```

3. **When the runtime finds a failure report without a `## Generalizable Learning` section**, it logs a warning: `"Failure report for {task} lacks a Generalizable Learning section."` This is non-blocking.

### Re-verification path

4. **When a file appears in `tasks/review/` that previously existed in `tasks/failed/`** (same filename), Verifier picks it up on its next heartbeat and performs a fresh verification against the original spec in `specs/archive/`. The re-verification is identical to a first verification — no bias from the prior failure. The prior failure report is preserved in git history.

5. **The move from `tasks/failed/` to `tasks/review/`** is a manual action. Only the human (or an agent with write access to both directories) initiates re-verification by moving the file. The runtime does not automate this transition.

### Skill update

6. **Builder proposes an updated `verification-protocol` skill** to `skills/proposed/verifier-verification-protocol/SKILL.md` that adds the `## Generalizable Learning` requirement to Verifier's failure flow. The updated skill instructs Verifier to: after writing the failure assessment, identify the generalizable pattern and write it as a dedicated section in the failure report.

## Interface Boundaries

### Failure report format (updated)

The existing failure report format gains one new required section:

```markdown
# Verification Report: {task-name}

spec: specs/archive/{task-name}.md
reviewed_at: {timestamp}
verdict: NOT SATISFIED ({score}/10)

## Summary
{existing content}

## Artifact-by-Artifact Assessment
{existing content}

## Satisfaction Score: {N}/10
{existing content}

## Path to Resolution
{existing content}

## Generalizable Learning
{NEW — the class of problem, why it occurred, and what to do differently}
```

### Runtime extraction

- Input: `tasks/failed/{task}.md` containing `## Generalizable Learning`
- Output: `learnings/failures/{YYYY-MM-DD}-{task}-verification-failure.md`
- Trigger: post-Verifier execution
- Deduplication: if the learning file already exists (by filename match), the runtime does not overwrite it

### Re-verification state transition

```
tasks/failed/{task}.md → (human moves) → tasks/review/{task}.md → (Verifier heartbeat) → tasks/verified/ OR tasks/failed/
```

## Constraints

- The `## Generalizable Learning` section must not simply restate the failure report's summary or path-to-resolution. It must identify the *class* of failure (e.g., "specs that require modifying human-only files") and a preventive recommendation.
- The runtime learning extraction is non-destructive — it creates a new file in `learnings/failures/` without modifying the failure report.
- The runtime warning for missing learning sections is non-blocking. The factory values observation over enforcement at this stage.
- Re-verification produces a complete new verification report. It does not append to or modify the prior failure report.
- Verifier does not need expanded write access. The runtime handles writing to `learnings/failures/`.

## Out of Scope

- Automated blocker detection. The system does not attempt to determine whether a failed task's blocker has been resolved.
- Changes to Verifier's access control in `agents.yaml`. The runtime extraction approach works within existing access boundaries.
- Builder's failure flow. This spec governs Verifier's failure output format and the runtime's extraction of learnings. Builder's own failure handling is governed by the `self-improvement` shared skill.
- Retroactive learning extraction from existing failure reports that predate this convention (though running the extraction manually on existing files would work if the section were added).

## Verification Criteria

- After Verifier fails a task with a `## Generalizable Learning` section, a corresponding file exists in `learnings/failures/`.
- The runtime logs a warning if Verifier writes a failure report without a `## Generalizable Learning` section.
- A task moved from `tasks/failed/` to `tasks/review/` is picked up by Verifier on its next heartbeat and receives a fresh verification report.
- The proposed updated `verification-protocol` skill exists in `skills/proposed/verifier-verification-protocol/SKILL.md` and includes the learning section requirement.
- The extracted learning file contains generalizable insight, not just a restatement of the failure summary.
