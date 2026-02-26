# the-role-description-ends-with-surface-knowledge-g
- severity: high
- status: open
- created: 2026-02-25T20:58:56
- source-agent: librarian
- source-type: needs-promotion

## Observation
The role description ends with "surface knowledge gaps to factory needs for the human." Since the `no-ephemeral-suggestions` spec shipped, `factory needs` is a specific CLI command that surfaces only blockers — observations no longer appear there. Knowledge gaps now surface via the `specs/factory-internal/` observation pipeline and are managed with `factory triage`. The current role description points to a dead-end path and would mislead a new operator reading agents.yaml.

## Context
Promoted from needs.md entry: librarian-role-description-factory-needs-ambiguity. Agent: librarian. Source file: memory/librarian/needs.md.
