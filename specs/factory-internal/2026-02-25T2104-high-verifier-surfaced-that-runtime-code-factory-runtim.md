# verifier-surfaced-that-runtime-code-factory-runtim
- severity: high
- status: open
- created: 2026-02-25T21:01:42Z
- source-agent: operator
- source-type: needs-promotion

## Observation
Verifier surfaced that runtime code (factory_runtime/) verification is trace-based (mental code reading), not execution-based. The factory runtime has no test harness — no isolated entry point for testing individual functions, no mock dispatch for backends. This is a structural gap: infrastructure code gets weaker verification than application code. When runtime bugs occur, they will have passed weaker scrutiny than builder-implemented code.

## Context
Promoted from needs.md entry: operator-verifier-observation-runtime-code-needs-tests. Agent: operator. Source file: memory/operator/needs.md.
