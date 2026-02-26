# my-review-protocol-step-1-performs-deduplication-a
- severity: high
- status: open
- created: 2026-02-25T21:04:00Z
- source-agent: reviewer
- source-type: needs-promotion

## Observation
My review-protocol (Step 1) performs deduplication against `specs/inbox/`, `specs/drafting/`, `specs/ready/`, `specs/archive/`. It does not include `specs/factory-internal/` in the deduplication scan, nor does it have a step for synthesizing thematically related factory-internal observations into consolidated improvement intents. After this evening's reflection passes, `specs/factory-internal/` contains 28 observations. Many are thematic duplicates: empty MEMORY.md appears 6 times (one per agent), missing daily logs appears 4+ times, available-vs-always skills appears 4+ times. My role is to "close the loop" — identify patterns and generate deduplicated intents. The protocol lacks the step that processes factory-internal observations into consolidated actions.

## Context
Promoted from needs.md entry: reviewer-no-factory-internal-synthesis-in-protocol. Agent: reviewer. Source file: memory/reviewer/needs.md.
