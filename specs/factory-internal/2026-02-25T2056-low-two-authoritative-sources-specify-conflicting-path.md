# two-authoritative-sources-specify-conflicting-path
- severity: low
- status: promoted
- promoted_to: specs/inbox/two-authoritative-sources-specify-conflicting-path.md
- promoted_at: 2026-02-26T07:09:35
- created: 2026-02-25T20:52:31
- source-agent: builder
- source-type: needs-promotion

## Observation
Two authoritative sources specify conflicting paths for builder-notes files. The `builder/implementation-approach` skill (step 8) says: `tasks/review/{task}/builder-notes.md` (subdirectory per task). The filesystem-conventions KNOWLEDGE.md entry says: `tasks/review/{task-name}.builder-notes.md` (flat file at review/ root). These are structurally different. A builder following the skill would write to a subdirectory; a builder following the naming convention would write a flat file. The verifier will look in one location; the builder may write to the other.

## Context
Promoted from needs.md entry: builder-notes-path-inconsistency. Agent: builder. Source file: memory/builder/needs.md.
