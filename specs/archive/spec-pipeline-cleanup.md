# spec-pipeline-cleanup

## Overview

The spec pipeline (inbox → drafting → ready → archive) accumulates stale files because no cleanup mechanism removes upstream copies after a spec advances downstream. The Spec agent can't delete from `specs/inbox/` (not in its `can_write`), and the existing `spec-lifecycle` convention doesn't mandate cleanup of earlier stages. This creates ambiguous pipeline state — stale files look like unprocessed work, confusing both agents and humans inspecting the pipeline.

This spec adds a post-execution cleanup step to the factory runtime that enforces a single-stage invariant: a spec file exists in at most one pipeline stage at a time.

## Behavioral Requirements

1. **When the factory runtime finishes executing any agent**, it runs a spec pipeline cleanup pass that checks for duplicate spec filenames across the four pipeline stages: `specs/inbox/`, `specs/drafting/`, `specs/ready/`, `specs/archive/`.

2. **When a spec filename exists in a downstream stage**, the cleanup pass removes matching files from all upstream stages. "Downstream" ordering is: inbox (earliest) → drafting → ready → archive (latest). Specifically:
   - For each filename in `specs/archive/`, remove matches from `specs/ready/`, `specs/drafting/`, and `specs/inbox/`.
   - For each filename in `specs/ready/`, remove matches from `specs/drafting/` and `specs/inbox/`.
   - For each filename in `specs/drafting/`, remove matches from `specs/inbox/`.

3. **When the cleanup pass deletes a file**, it logs the action: `"Cleaned stale spec: specs/inbox/foo.md (exists in specs/archive/)"`.

4. **The cleanup pass is also available as a standalone CLI command** (e.g., `factory cleanup-specs`) so it can be run manually outside of agent execution.

## Interface Boundaries

### Directories involved

- `specs/inbox/` — raw intents from human or reviewer
- `specs/drafting/` — Spec agent is working on these
- `specs/ready/` — specced and awaiting Builder
- `specs/archive/` — terminal state, completed specs

### Matching criterion

Exact filename match. `foo.md` in `specs/archive/` causes deletion of `foo.md` in `specs/inbox/`, `specs/drafting/`, and `specs/ready/`. Versioned archives (e.g., `foo.v1.md`) are **not** considered matches for `foo.md`.

### CLI interface

```
factory cleanup-specs          # Run the cleanup pass manually
factory cleanup-specs --dry-run  # Show what would be cleaned without deleting
```

### Integration point

The cleanup pass runs as the final step after agent execution completes in the runtime's agent lifecycle. It runs regardless of which agent was executed. It does not depend on agent-level access control — the runtime has full filesystem access.

## Constraints

- The cleanup pass must **never delete a file from a downstream stage**. It only removes upstream copies.
- The cleanup pass must **never delete a file that has no downstream match**. A spec in `specs/inbox/` with no copy in `specs/drafting/`, `specs/ready/`, or `specs/archive/` is untouched.
- Archive files are **never deleted** by this process. Archive is a terminal state.
- The cleanup pass must be **idempotent** — running it multiple times produces the same result as running it once.
- The cleanup pass should complete in under 1 second for a typical pipeline with tens of spec files.

## Out of Scope

- Access control changes to `agents.yaml`. This spec solves cleanup at the runtime level, not the access level.
- Changes to how agents write files. Agents continue to copy files to downstream directories as they do now.
- Cleanup of non-spec pipeline directories (e.g., `tasks/`). That is a separate concern with different lifecycle rules.
- Git commits for cleanup deletions. The cleanup pass modifies the working tree; the agent's normal commit behavior handles persistence.

## Verification Criteria

- After running the Spec agent on an inbox intent, the intent file no longer exists in `specs/inbox/` (cleaned up because a copy exists in `specs/drafting/` or later).
- After running the Builder agent on a ready spec, the spec no longer exists in `specs/ready/` (cleaned up because a copy exists in `specs/archive/`).
- A spec that exists only in `specs/inbox/` (not yet picked up) is not deleted by the cleanup pass.
- Running `factory cleanup-specs` removes the currently stale files: `pipeline-next-step.md` and `self-review-loop.md` in both `specs/inbox/` and `specs/drafting/`.
- Running `factory cleanup-specs --dry-run` lists the files that would be cleaned without deleting them.
