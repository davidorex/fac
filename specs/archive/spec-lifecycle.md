# spec-lifecycle

## Overview

Specs currently disappear from the filesystem after Builder picks them up. When Verifier runs, it cannot find the original spec to verify the artifact against — it has to reconstruct intent from Builder's self-reported criteria. This worked for a trivial hello-world task but will fail on anything with nuanced acceptance criteria.

This spec defines the lifecycle of a spec file as it moves through the factory pipeline, ensuring the original spec is always available to Verifier (and to any agent that needs to reference past work).

## Behavioral Requirements

1. **When Builder picks up a spec from `specs/ready/`**, Builder copies the spec file to `specs/archive/` (preserving the original filename) **before** beginning any implementation work. Builder then removes the file from `specs/ready/`. The copy-then-remove order is mandatory — if the archive copy fails, the spec must remain in `specs/ready/`.

2. **When Verifier evaluates completed work**, Verifier looks up the original spec in `specs/archive/{spec-name}.md` and verifies the artifact against the spec's behavioral requirements, interface boundaries, constraints, and verification criteria. Verifier references the archive path (not `specs/ready/`) in its review report.

3. **When Builder writes its review/task file to `tasks/review/`**, the task file includes a `spec_archive` field pointing to the archived spec's path (e.g., `specs/archive/hello-world.md`). This gives Verifier an explicit pointer rather than requiring a filename-convention guess.

## Interface Boundaries

### File paths

- Source: `specs/ready/{name}.md`
- Archive destination: `specs/archive/{name}.md` (same filename, different directory)
- Reference in task file: `spec_archive: specs/archive/{name}.md`

### State transitions

The spec lifecycle adds one new transition to the existing protocol:

```
specs/inbox/       → specs/drafting/    (Spec picks up intent)
specs/drafting/    → specs/ready/       (Spec finishes, ready for Builder)
specs/ready/       → specs/archive/     (Builder archives before building)
```

`specs/archive/` is a terminal state. Archived specs are never moved or deleted by any agent.

## Constraints

- **No spec may be deleted from the filesystem by any agent.** Specs move between directories; they do not disappear. The only path out of existence is human-initiated cleanup.
- **Builder must not begin implementation until the archive copy is confirmed.** This is the ordering guarantee that prevents the Verifier-blind-spot observed in the hello-world task.
- **Archive filenames must match the original filename exactly.** No timestamps, no prefixes, no renaming. The name is the stable identifier across the pipeline.
- **If `specs/archive/{name}.md` already exists** (a re-spec of the same name), Builder renames the existing archive to `specs/archive/{name}.v{N}.md` where N is the next integer (starting at 1), then archives the new spec under the original name. This preserves history without breaking the current-spec lookup convention.

## Out of Scope

- Spec content format changes. This spec governs file lifecycle, not file contents.
- Automated tooling to enforce the archive step. This is a convention that agents follow. Enforcement tooling (if desired) would be a separate spec.
- Cleanup or retention policies for `specs/archive/`. The archive grows indefinitely until a human decides otherwise.

## Verification Criteria

- After Builder completes any task, `specs/archive/` contains the original spec file with the matching name.
- Verifier's review report references the spec via its `specs/archive/` path and performs criterion-by-criterion verification against the original spec text.
- `specs/ready/` does not contain a spec that Builder has already picked up and archived.
- If a spec is re-issued with the same name, the previous version exists in archive with a `.v{N}.md` suffix and the current version exists at the canonical `{name}.md` path.
