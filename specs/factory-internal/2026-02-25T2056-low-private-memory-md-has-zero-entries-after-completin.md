# private-memory-md-has-zero-entries-after-completin
- severity: low
- status: promoted
- promoted_to: specs/inbox/private-memory-md-has-zero-entries-after-completin.md
- promoted_at: 2026-02-26T07:09:35
- created: 2026-02-25T20:52:31
- source-agent: builder
- source-type: needs-promotion

## Observation
Private MEMORY.md has zero entries after completing 3+ tasks (hello-world-python, multi-cli-backend-support, no-ephemeral-suggestions). Each new builder session starts cold with no curated knowledge. Builder-specific patterns, factory conventions discovered during implementation, and tool quirks (e.g., the `rm` interactive alias) are not being preserved in the builder's own memory — they exist only in shared KNOWLEDGE.md or git history.

## Context
Promoted from needs.md entry: builder-empty-private-memory. Agent: builder. Source file: memory/builder/needs.md.
