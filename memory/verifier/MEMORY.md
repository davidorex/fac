# Verifier — Private Memory

## Scoring Calibration (as of 2026-02-25)

Three tasks verified, all passed:
- **hello-world-python** (10/10): Trivial spec, trivial implementation, all 6 criteria directly executable. 10/10 because zero gap between spec and output.
- **multi-cli-backend-support** (9/10): Complex infrastructure refactor, 9 criteria, all satisfied. 1-point deduction for cosmetic dead variable carried from original code. Verification was trace-based (no runtime test harness).
- **no-ephemeral-suggestions** (9/10): Complex kernel feature, 14 criteria, all satisfied. 1-point deduction for body-text truncation in fallback extraction path. Verification was trace-based.

**Pattern:** My 9/10 deductions have been for pre-existing cosmetic issues or minor data-quality gaps in edge paths. This feels like accurate calibration — these are real observations but not satisfaction-reducing for most operators. A 10/10 means "zero observations of any kind," which is a high bar.

## Verification Strategy by Task Type

- **Application code** (hello-world-python): Direct execution. Run the artifact, verify output byte-for-byte, check permissions, use py_compile. Highest confidence.
- **Infrastructure/runtime code** (multi-cli-backend, no-ephemeral-suggestions): Code tracing. Read the implementation, verify structural properties (imports, signatures, control flow), check integration points. Lower confidence — reasoning errors possible.

## Effective Practices

- Criterion-by-criterion assessment format works well — forces systematic coverage, prevents skipping criteria.
- Minor observations (non-blocking issues) documented in reports serve as signal without failing the task.
- Meta-scenario directional assessment adds value — contextualizes the task in the larger factory trajectory.
- Always noting absent holdout scenarios explicitly rather than silently passing.

## Skills I Actually Use

- verification-protocol: Every run. Defines the report format.
- satisfaction-scoring: Every run. Defines the metric.
- scenario-evaluation: Every run. Even when no scenarios exist, the absence is documented.
- verification-with-scenarios: Every run (by direct file read, not by skill activation — it's not in agents.yaml).
- failure-reporting: Never used. No failures yet.
- decomposition: Never used. No task has required parallel subagent work.
- nanoclaw-whatsapp: Never directly invoked. Kernel handles notifications automatically.
