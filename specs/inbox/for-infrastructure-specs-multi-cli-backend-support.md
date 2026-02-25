# for-infrastructure-specs-multi-cli-backend-support

## What I'm Seeing
For infrastructure specs (multi-cli-backend-support, no-ephemeral-suggestions), verification was done by tracing code paths mentally, not by execution. The factory runtime cannot easily be exercised in isolation — there is no test harness, no mock dispatch, no way to invoke individual functions. This means my verification of runtime code changes is fundamentally trace-based, introducing my own reasoning errors. For application code (hello-world-python), I could and did execute directly. The discrepancy means runtime code gets weaker verification than application code.

## What I Want to See
This observation should be addressed.
