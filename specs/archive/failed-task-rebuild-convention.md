# failed-task-rebuild-convention

## Overview

When a task fails verification due to build quality — the spec was correct but the artifacts don't meet its constraints — the pipeline has no mechanism to return work to Builder for rebuild. The factory blueprint envisions Builder iterating on failures ("Builder will use this to iterate," `universe/synthesis/factory-blueprint.md` line 498), but the access model prevents it: Builder cannot read `tasks/failed/` or `specs/archive/`, and the spec-lifecycle convention (`specs/archive/spec-lifecycle.md`) declares archive as a terminal state.

The `failure-learning-convention` (`specs/archive/failure-learning-convention.md`) defines a re-verification path (`tasks/failed/` → `tasks/review/`) for cases where the existing artifacts should pass after a blocker is resolved. But re-verification re-checks the same artifacts — it cannot produce different results when the artifacts themselves need modification.

This spec establishes the rebuild path: a human-initiated convention that returns a correctly-specced but incorrectly-built task to Builder through the existing `specs/ready/` intake, with failure context attached so Builder knows what to fix. This complements (not replaces) the re-verification path — the two paths address different failure modes.

## Behavioral Requirements

### Distinguishing rebuild from re-verification

1. **When Verifier writes a failure report**, the `## Path to Resolution` section implicitly indicates the recovery mode. If the resolution requires modifying artifacts (e.g., "Builder should trim each of the 11 failing skills"), the task is a rebuild candidate. If the resolution is waiting for an external blocker to resolve (e.g., "human must add entry to agents.yaml"), the task is a re-verification candidate. The failure-learning-convention governs re-verification. This spec governs rebuild.

2. **The human decides whether to trigger a rebuild.** No automated rule distinguishes rebuild from re-verification — the distinction depends on judgment about whether the artifacts or the environment need to change. The runtime provides a CLI command to execute the rebuild transition; the human decides when to invoke it.

### Triggering a rebuild

3. **When a human runs `factory rebuild {task-name}`**, the runtime performs the following in order:

   a. **Validates prerequisites.** `specs/archive/{task-name}.md` must exist (the spec was correctly specced and archived). `tasks/failed/{task-name}.md` must exist (the task has a current failure report). If either is missing, the command prints an error message naming the missing file and exits without modifying the filesystem.

   b. **Copies the spec back to ready.** The runtime copies `specs/archive/{task-name}.md` to `specs/ready/{task-name}.md`. The archive copy is not removed — `specs/archive/` remains terminal as defined by spec-lifecycle. This is a copy, not a move.

   c. **Versions the failure report.** The runtime renames `tasks/failed/{task-name}.md` to `tasks/failed/{task-name}.v{N}.md`, where N is the next available integer (starting at 1). This clears the active failure slot so a potential new failure from the rebuild attempt doesn't conflict with the prior report.

   d. **Writes a rebuild brief.** The runtime reads the versioned failure report (`tasks/failed/{task-name}.v{N}.md`), extracts the `## Path to Resolution` section (everything from that heading to the next `##` heading or end of file), and writes it to `specs/ready/{task-name}.rebuild.md` in this format:

   ```markdown
   # Rebuild Brief: {task-name}

   prior_failure: tasks/failed/{task-name}.v{N}.md
   prior_score: {extracted from the Satisfaction Score heading}

   ## What to Fix
   {content of the ## Path to Resolution section from the failure report}
   ```

   e. **Prints a summary.** The command outputs: the spec path placed in ready/, the rebuild brief path, and the versioned failure report path.

### Builder behavior on rebuild

4. **When Builder picks up a spec from `specs/ready/` that has a companion `{task-name}.rebuild.md` file**, Builder reads both the spec and the rebuild brief before beginning work. The rebuild brief's `## What to Fix` section provides specific remediation guidance from Verifier. Builder modifies the existing artifacts (rather than creating from scratch) to address the identified failures while maintaining all other spec constraints.

5. **When Builder picks up a spec from `specs/ready/` that has no companion `.rebuild.md` file**, Builder proceeds with normal first-build behavior. The presence of a `.rebuild.md` file is the sole signal distinguishing rebuild from first build.

6. **After completing the rebuild**, Builder follows the normal post-build flow: archive the spec (spec-lifecycle versioning handles the existing archive copy), write the task to `tasks/review/`, and clean up `specs/ready/` including both the spec and the `.rebuild.md` file.

### Runtime cleanup

7. **When the `spec-pipeline-cleanup` mechanism runs** (as defined in `specs/archive/spec-pipeline-cleanup.md`), it treats `.rebuild.md` files identically to spec files for staleness detection — if a rebuild brief exists in `specs/ready/` but the corresponding spec has already been archived, the rebuild brief is stale and should be removed.

## Interface Boundaries

### CLI command

```
factory rebuild {task-name}

Arguments:
  task-name    The name of the task (matching the filename without .md extension
               in both specs/archive/ and tasks/failed/)

Behavior:
  - Copies specs/archive/{task-name}.md → specs/ready/{task-name}.md
  - Extracts Path to Resolution from failure report → specs/ready/{task-name}.rebuild.md
  - Renames tasks/failed/{task-name}.md → tasks/failed/{task-name}.v{N}.md
  - Commits all file changes to git

Exit codes:
  0  Rebuild triggered successfully
  1  Missing spec in specs/archive/ or missing failure report in tasks/failed/
  2  Spec already exists in specs/ready/ (rebuild or first build in progress)
```

### Rebuild brief format

```markdown
# Rebuild Brief: {task-name}

prior_failure: tasks/failed/{task-name}.v{N}.md
prior_score: {N}/10

## What to Fix
{Verbatim content of the ## Path to Resolution section from the failure report}
```

### State transitions

The rebuild path adds one new cycle to the pipeline:

```
tasks/failed/{task}.md      → (factory rebuild)  → tasks/failed/{task}.v{N}.md
specs/archive/{task}.md     → (factory rebuild)  → specs/ready/{task}.md (copy)
                                                  + specs/ready/{task}.rebuild.md (new)
specs/ready/{task}.md       → (Builder picks up)  → normal build/archive/review flow
specs/ready/{task}.rebuild.md → (Builder picks up) → removed after build
```

### File locations

| File | Directory | Purpose |
|------|-----------|---------|
| Spec (authoritative) | `specs/archive/` | Unchanged, stays terminal |
| Spec (rebuild copy) | `specs/ready/` | Builder intake, archived on build |
| Rebuild brief | `specs/ready/` | Failure context for Builder, removed after build |
| Prior failure (versioned) | `tasks/failed/` | Preserved history |
| New task (post-rebuild) | `tasks/review/` | Normal Verifier intake |

## Constraints

- **Human-initiated only.** The runtime does not automatically trigger rebuilds. The human runs `factory rebuild` or manually performs the file operations. Automated rebuild would create a loop (build → fail → rebuild → fail → ...) with no human judgment about whether to revise the spec instead.
- **One rebuild at a time per task.** If `specs/ready/{task-name}.md` already exists when `factory rebuild` is invoked, the command prints a warning ("spec already in ready/ — rebuild or first build may be in progress") and exits without modifying the filesystem.
- **Spec content is unchanged.** The rebuild uses the same spec as the original build. If the spec itself needs revision (e.g., the constraint was unrealistic), the correct path is re-speccing through `specs/inbox/`, not rebuilding.
- **Rebuild brief is extracted, not authored.** The runtime extracts from the failure report mechanically. It does not summarize, interpret, or add guidance. Builder receives Verifier's exact words.
- **Multiple rebuild cycles are supported.** Each `factory rebuild` invocation versions the current failure report (.v1, .v2, etc.) and generates a fresh rebuild brief. There is no limit on rebuild cycles — the human decides when to stop or re-spec.
- **Failure report must have extractable sections.** If `tasks/failed/{task-name}.md` lacks a `## Path to Resolution` section, the runtime falls back to extracting the `## Summary` section instead. If neither section exists, the `## What to Fix` section contains the full text of the failure report (Builder cannot read `tasks/failed/` directly, so the rebuild brief must be self-contained). The rebuild still proceeds — the missing section is non-blocking. If the failure report lacks a satisfaction score, the `prior_score` field in the rebuild brief is written as `prior_score: unknown`.

## Out of Scope

- **Automatic detection of rebuild-vs-re-verify.** Distinguishing failure modes requires judgment. The human decides which recovery path to take.
- **Builder access to `tasks/failed/`.** The rebuild brief sidesteps Builder's access boundary by extracting failure context into `specs/ready/`, which Builder can read. Expanding Builder's `can_read` is a separate access-model concern.
- **Builder access to `specs/archive/`.** Same approach — the convention copies the spec to `specs/ready/` rather than requiring Builder to read archive.
- **Changes to `agents.yaml`.** This convention works within existing access boundaries.
- **Re-verification path changes.** The `failure-learning-convention`'s re-verification path (`tasks/failed/` → `tasks/review/`) remains valid for blocker-resolved failures. The two paths are complementary.

## Verification Criteria

- After running `factory rebuild {task-name}`, `specs/ready/{task-name}.md` exists and matches `specs/archive/{task-name}.md` in content.
- After running `factory rebuild {task-name}`, `specs/ready/{task-name}.rebuild.md` exists and its `## What to Fix` section matches the failure report's `## Path to Resolution` section.
- After running `factory rebuild {task-name}`, `tasks/failed/{task-name}.md` has been renamed to `tasks/failed/{task-name}.v{N}.md` and the original filename no longer exists.
- Running `factory rebuild` with a missing spec or missing failure report prints an error and modifies no files.
- Running `factory rebuild` when a spec is already in `specs/ready/` prints a warning and modifies no files.
- Builder, upon finding a `.rebuild.md` companion file, reads it and uses the guidance to modify existing artifacts (observable from Builder's daily log or commit messages referencing the rebuild brief).
- The complete cycle works: `factory rebuild` → Builder picks up → Builder writes to `tasks/review/` → Verifier verifies.
