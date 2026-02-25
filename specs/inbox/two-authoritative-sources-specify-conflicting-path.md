# two-authoritative-sources-specify-conflicting-path

## What I'm Seeing
Two authoritative sources specify conflicting paths for builder-notes files. The `builder/implementation-approach` skill (step 8) says: `tasks/review/{task}/builder-notes.md` (subdirectory per task). The filesystem-conventions KNOWLEDGE.md entry says: `tasks/review/{task-name}.builder-notes.md` (flat file at review/ root). These are structurally different. A builder following the skill would write to a subdirectory; a builder following the naming convention would write a flat file. The verifier will look in one location; the builder may write to the other.

## What I Want to See
This observation should be addressed.
