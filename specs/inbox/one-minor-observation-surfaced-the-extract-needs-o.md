# one-minor-observation-surfaced-the-extract-needs-o

## What I'm Seeing
One minor observation surfaced: the `_extract_needs_observation()` fallback path truncates body text at 300 characters, which affected the 3 migrated reviewer entries. Full text is preserved in the original needs.md and reachable via the `## Context` section reference. Not a functional failure — a polish gap in a fallback code path for non-standard entry formats.

## What I Want to See
This observation should be addressed.
