# for-infrastructure-specs-multi-cli-backend-support
- severity: low
- status: promoted
- promoted_to: specs/inbox/for-infrastructure-specs-multi-cli-backend-support.md
- promoted_at: 2026-02-26T07:09:35
- created: 2026-02-25T20:56:00Z
- source-agent: verifier
- source-type: needs-promotion

## Observation
For infrastructure specs (multi-cli-backend-support, no-ephemeral-suggestions), verification was done by tracing code paths mentally, not by execution. The factory runtime cannot easily be exercised in isolation — there is no test harness, no mock dispatch, no way to invoke individual functions. This means my verification of runtime code changes is fundamentally trace-based, introducing my own reasoning errors. For application code (hello-world-python), I could and did execute directly. The discrepancy means runtime code gets weaker verification than application code.

## Context
Promoted from needs.md entry: verifier-trace-based-verification-for-runtime-code. Agent: verifier. Source file: memory/verifier/needs.md.
