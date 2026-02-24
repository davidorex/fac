spec: spec-lifecycle
spec_archive: specs/archive/spec-lifecycle.md
status: ready-for-review
built_by: builder
date: 2026-02-24

## Summary

This spec defines a behavioral convention — no code artifact. The implementation is the protocol itself, now established in Builder's memory and applied during this very task.

## What Was Done

1. **Archived** the spec to `specs/archive/spec-lifecycle.md` before beginning any implementation work (following the ordering guarantee defined in the spec).
2. **Removed** `specs/ready/spec-lifecycle.md` after confirming the archive copy succeeded.
3. **Updated** `memory/builder/MEMORY.md` with the new spec lifecycle protocol so future Builder sessions apply it consistently.
4. This review task includes the `spec_archive` field as required by Behavioral Requirement 3.

## Verification Criteria (from spec)

1. After Builder completes any task, `specs/archive/` contains the original spec file with the matching name.
   - **Evidence:** `specs/archive/spec-lifecycle.md` exists and matches the original spec content exactly.

2. Verifier's review report references the spec via its `specs/archive/` path and performs criterion-by-criterion verification against the original spec text.
   - **Evidence:** This task file provides `spec_archive: specs/archive/spec-lifecycle.md` as the explicit pointer. Verifier should use this path.

3. `specs/ready/` does not contain a spec that Builder has already picked up and archived.
   - **Evidence:** `specs/ready/spec-lifecycle.md` has been removed.

4. If a spec is re-issued with the same name, the previous version exists in archive with a `.v{N}.md` suffix and the current version exists at the canonical `{name}.md` path.
   - **Evidence:** Not applicable to this task (no pre-existing archive). The versioning logic is encoded in Builder's memory for future application.
