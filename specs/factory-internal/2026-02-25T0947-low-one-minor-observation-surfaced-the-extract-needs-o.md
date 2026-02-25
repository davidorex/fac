# one-minor-observation-surfaced-the-extract-needs-o
- severity: low
- status: open
- created: 2026-02-25T09:47:53
- source-agent: verifier
- source-type: kernel-extraction

## Observation
One minor observation surfaced: the `_extract_needs_observation()` fallback path truncates body text at 300 characters, which affected the 3 migrated reviewer entries. Full text is preserved in the original needs.md and reachable via the `## Context` section reference. Not a functional failure — a polish gap in a fallback code path for non-standard entry formats.

## Context
Extracted by kernel from agent response prose (agent did not write to needs.md during this run).
