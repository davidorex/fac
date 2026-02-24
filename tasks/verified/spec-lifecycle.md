spec: spec-lifecycle
spec_archive: specs/archive/spec-lifecycle.md
status: verified
verified_by: verifier
date: 2026-02-24

## Verification Report

Verified against original spec at `specs/archive/spec-lifecycle.md`.

### Behavioral Requirements — Criterion-by-Criterion

**BR1: Builder archives spec before implementation, then removes from ready.**
- PASS. Git commit `cbb00d0` shows `specs/{ready => archive}/spec-lifecycle.md` as a rename with 100% similarity index — content is byte-identical to the original. The archive happened in the same commit as the implementation work (memory update, review task creation). Since the spec is a behavioral convention with no code artifact, this is the earliest possible moment. The ordering guarantee is satisfied: archive is confirmed, ready is clear.

**BR2: Verifier looks up spec in `specs/archive/` and verifies against it.**
- PASS (meta). This report references and was verified against `specs/archive/spec-lifecycle.md`. All criteria below are evaluated against the original spec text, not Builder's self-reported summary.

**BR3: Task file includes `spec_archive` field.**
- PASS. `tasks/review/spec-lifecycle.md` contains `spec_archive: specs/archive/spec-lifecycle.md` on line 2.

### Verification Criteria

1. **`specs/archive/` contains the original spec file with matching name.**
   - PASS. `specs/archive/spec-lifecycle.md` exists. Git diff confirms 100% content identity with the original `specs/ready/spec-lifecycle.md`.

2. **Verifier's review report references spec via archive path.**
   - PASS. This report fulfills this criterion.

3. **`specs/ready/` does not contain a spec Builder has already picked up.**
   - PASS. `specs/ready/spec-lifecycle.md` does not exist. Directory confirmed empty.

4. **Re-issue versioning (`.v{N}.md` suffix).**
   - N/A. No pre-existing archive existed. Versioning logic is encoded in Builder's memory for future application.

### Additional Checks

- **Builder memory updated:** `memory/builder/MEMORY.md` contains the spec lifecycle protocol with correct archive-before-build ordering, spec_archive field requirement, and versioning logic. Protocol is accurately captured.
- **Constraints compliance:** No spec was deleted (rename = move). Archive filename matches original exactly. Archive is terminal state.

### Verdict

**PASS** — All applicable verification criteria satisfied. The behavioral convention is correctly established and Builder's memory encodes the protocol for future sessions.
