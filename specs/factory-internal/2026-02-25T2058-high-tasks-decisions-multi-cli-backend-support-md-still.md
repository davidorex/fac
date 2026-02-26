# tasks-decisions-multi-cli-backend-support-md-still
- severity: high
- status: open
- created: 2026-02-25T20:56:00Z
- source-agent: verifier
- source-type: needs-promotion

## Observation
tasks/decisions/multi-cli-backend-support.md still exists as a resolved decision gate. The 4 GC passes (cleanup-specs, cleanup-tasks, cleanup-research, cleanup-factory-internal) do not cover tasks/decisions/. Resolved decisions accumulate indefinitely. Currently there is only 1, but this directory will grow with every spec that hits a hard gate.

## Context
Promoted from needs.md entry: verifier-decisions-directory-no-gc. Agent: verifier. Source file: memory/verifier/needs.md.
