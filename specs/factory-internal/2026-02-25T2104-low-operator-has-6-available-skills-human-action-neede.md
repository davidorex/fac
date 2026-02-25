# operator-has-6-available-skills-human-action-neede
- severity: low
- status: promoted
- promoted_to: specs/inbox/operator-has-6-available-skills-human-action-neede.md
- promoted_at: 2026-02-26T07:09:35
- created: 2026-02-25T21:01:42Z
- source-agent: operator
- source-type: needs-promotion

## Observation
Operator has 6 available skills (human-action-needed, decomposition, nanoclaw-whatsapp, git-workflow, ci-cd, dependency-management, monitoring) that are directly relevant to "keep the lights on" role, but I have never activated any of them. This is architectural: operator should have these loaded at start of each session if they address ongoing monitoring needs. CI/CD, dependency-management, and monitoring directly support infrastructure health checks — core to operator function.

## Context
Promoted from needs.md entry: operator-available-skills-not-activated. Agent: operator. Source file: memory/operator/needs.md.
