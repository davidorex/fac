# Verifier — Needs

## verifier-empty-private-memory-after-three-verifications
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T2058-high-private-memory-md-is-empty-no-entries-yet-after-3.md
- created: 2026-02-25T20:56:00Z
- category: observation
- blocked: Private MEMORY.md is empty ("No entries yet") after 3 completed verifications (hello-world-python 10/10, multi-cli-backend-support 9/10, no-ephemeral-suggestions 9/10). This means every verification session starts with zero accumulated knowledge — no scoring calibration notes, no pattern recognition across tasks, no record of what I've found effective. I rediscover context each time rather than building on it.
- context: Reflection pass. Read memory/verifier/MEMORY.md, found it has only the placeholder text from initial creation.

### Exact Change
After each verification, the Verifier (or the kernel post-run pass) should prompt or auto-append durable findings to MEMORY.md: scoring calibration observations, common spec-to-implementation mismatches, effective verification strategies. Alternatively, the runtime could inject a reminder to curate private memory at the end of verification runs.

## verifier-no-daily-logs-written
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T2058-low-memory-daily-verifier-contains-zero-log-files-the.md
- created: 2026-02-25T20:56:00Z
- category: observation
- blocked: memory/daily/verifier/ contains zero log files. The context-discipline skill says to write daily logs as checkpoints and task summaries. After 3 verification tasks across a full day, there should be at least one daily log. Without logs there is no audit trail of reasoning, no checkpointing for long tasks, and no way to detect scoring calibration drift over time.
- context: Reflection pass. Globbed memory/daily/verifier/*.md, found no files.

### Exact Change
The Verifier should write a daily log entry after each verification task. This could be reinforced by adding a post-verification step to the verification-protocol skill, or the runtime could inject a daily-log reminder into the system prompt.

## verifier-unlisted-skill-verification-with-scenarios
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T2058-low-the-file-skills-verifier-verification-with-scenari.md
- created: 2026-02-25T20:56:00Z
- category: observation
- blocked: The file skills/verifier/verification-with-scenarios/SKILL.md exists and contains substantive guidance on integrating scenario evaluation into verification reports. However, agents.yaml does not list it in the verifier's available skills (only lists verification-protocol, satisfaction-scoring, scenario-evaluation, failure-reporting). The runtime would not surface it as an available skill to load. Its guidance overlaps with scenario-evaluation but adds specific formatting requirements (when to include the section, meta-scenario handling) that the other skill doesn't cover.
- context: Reflection pass. Globbed skills/verifier/**/* and compared against agents.yaml skills list.

### Exact Change
Either add `verifier/verification-with-scenarios` to the verifier's `available:` skills in agents.yaml, or merge its unique content (the meta-scenario directive, the "without scenarios" fallback language) into the existing scenario-evaluation skill and remove the orphaned file.

## verifier-no-failure-path-exercised
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T2058-low-all-3-verifications-to-date-have-passed-scores-10.md
- created: 2026-02-25T20:56:00Z
- category: observation
- blocked: All 3 verifications to date have passed (scores 10, 9, 9). The failure-reporting skill, the NOT SATISFIED workflow, and the rebuild path (factory rebuild) have never been exercised. This means: (1) failure report format has no real-world validation, (2) the Generalizable Learning extraction by the runtime has never triggered, (3) there is no calibration data for what a failing task looks like in this factory. The first actual failure will be the first time the full rejection workflow runs end-to-end.
- context: Reflection pass. Checked tasks/failed/ (only .gitkeep), learnings/failures/ (empty), and tasks/resolved/ (only .gitkeep).

### Exact Change
This is an observation, not a request. The natural path is to wait for a genuine failure. However, if the operator wants to validate the failure path proactively, a deliberately-failing spec (spec that cannot be satisfied, or a build that intentionally misses criteria) would exercise: failure-reporting format, Generalizable Learning extraction, factory rebuild flow, and re-verification.

## verifier-trace-based-verification-for-runtime-code
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T2058-low-for-infrastructure-specs-multi-cli-backend-support.md
- created: 2026-02-25T20:56:00Z
- category: observation
- blocked: For infrastructure specs (multi-cli-backend-support, no-ephemeral-suggestions), verification was done by tracing code paths mentally, not by execution. The factory runtime cannot easily be exercised in isolation — there is no test harness, no mock dispatch, no way to invoke individual functions. This means my verification of runtime code changes is fundamentally trace-based, introducing my own reasoning errors. For application code (hello-world-python), I could and did execute directly. The discrepancy means runtime code gets weaker verification than application code.
- context: Reflection pass. Reviewed own verification reports — hello-world-python used direct execution (xxd, py_compile, ./hello_world.py), while multi-cli-backend-support and no-ephemeral-suggestions used code reading and structural analysis.

### Exact Change
A test harness for factory_runtime (even minimal — import checks, function signature validation, mock dispatch for backends) would allow the Verifier to execute rather than trace. This is architectural: the runtime currently has no tests directory and no entry point for isolated function testing.

## verifier-decisions-directory-no-gc
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T2058-high-tasks-decisions-multi-cli-backend-support-md-still.md
- created: 2026-02-25T20:56:00Z
- category: observation
- blocked: tasks/decisions/multi-cli-backend-support.md still exists as a resolved decision gate. The 4 GC passes (cleanup-specs, cleanup-tasks, cleanup-research, cleanup-factory-internal) do not cover tasks/decisions/. Resolved decisions accumulate indefinitely. Currently there is only 1, but this directory will grow with every spec that hits a hard gate.
- context: Reflection pass. Listed tasks/decisions/ and found a resolved decision file still present. Checked KNOWLEDGE.md for GC pass coverage — decisions/ not mentioned.

### Exact Change
Add a 5th GC pass (cleanup-decisions) that removes tasks/decisions/ files when the corresponding spec is archived and all entries are resolved. Or define a lifecycle for decisions — e.g., move to tasks/decisions/resolved/ after the spec clears verification.
