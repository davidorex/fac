# tasks-decisions-multi-cli-backend-support-md-conta
- severity: low
- status: promoted
- promoted_to: specs/inbox/tasks-decisions-multi-cli-backend-support-md-conta.md
- promoted_at: 2026-02-26T07:09:35
- created: 2026-02-25T21:01:42Z
- source-agent: operator
- source-type: needs-promotion

## Observation
tasks/decisions/multi-cli-backend-support.md contains duplicate entries for decisions 7.1, 7.2, and 7.3. For each decision, there is one entry marked "resolved" or "auto-resolved" with a decided answer, and immediately below it is a duplicate entry marked "open" with the same decision ID but without resolution. This creates ambiguity about state and may confuse `factory decide` command if it scans for unresolved entries.

## Context
Promoted from needs.md entry: operator-decision-file-duplicate-entries. Agent: operator. Source file: memory/operator/needs.md.
