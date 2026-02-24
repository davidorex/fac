# Review Task: failure-learning-convention

spec_archive: specs/archive/failure-learning-convention.md
built_at: 2026-02-24T11:43:44
built_by: builder

## Deliverables

### 1. `extract_failure_learnings(workspace)` function in `runtime/factory_runtime/cli.py`

Scans `tasks/failed/*.md` for a `## Generalizable Learning` section.
For each matching file:
- If no corresponding learning exists in `learnings/failures/` (matched by task name substring), writes
  `learnings/failures/{YYYY-MM-DD}-{task-name}-verification-failure.md` with the specified format.
- Deduplication: does not overwrite existing learning files.

For failure reports missing the section, logs a non-blocking warning.
Returns list of log lines.

### 2. Post-verifier hook in the `run` command

After spec pipeline cleanup, when `agent == "verifier"`, calls `extract_failure_learnings()`.
Warnings printed as yellow. Extraction confirmations printed as dim.

### 3. `skills/proposed/verifier-verification-protocol/SKILL.md`

Updated verification protocol skill instructing Verifier to include a `## Generalizable Learning`
section in every failure report. Includes: section requirements, what makes a good generalizable
learning, re-verification protocol.

## Implementation Location

- `runtime/factory_runtime/cli.py`
- `skills/proposed/verifier-verification-protocol/SKILL.md`

## Verification Criteria (from spec)

- After Verifier fails a task with a `## Generalizable Learning` section, a corresponding file exists in `learnings/failures/`
- The runtime logs a warning if Verifier writes a failure report without the section
- A task moved from `tasks/failed/` to `tasks/review/` is picked up by Verifier on its next heartbeat
- The proposed skill exists at `skills/proposed/verifier-verification-protocol/SKILL.md` and includes the learning section requirement
- The extracted learning file contains generalizable insight, not just a restatement
