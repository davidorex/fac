# Librarian — Private Memory

## Pipeline Validation State (as of 2026-02-25)

**Tested path:** spec → build → verify (happy path, no ambiguities, 10/10 score — hello-world-python)
**Factory internal specs also verified:** multi-cli-backend-support (9/10), no-ephemeral-suggestions (9/10)
**Hard gate path confirmed:** multi-cli-backend-support decision 7.1 exercised the full hard gate cycle — `tasks/decisions/` file written, operator resolved via `factory decide`, pipeline resumed. KNOWLEDGE.md conventions for this path are confirmed operational, not aspirational.
**Failure workflow functions validated:** `failure-path-fire-drill` (verified 2026-02-26) added `factory fire-drill` which programmatically exercises `extract_failure_learnings()`, `rebuild_task()`, and `resolve_completed_failures()` with synthetic data. These three functions are confirmed structurally sound. Note: the *real* rebuild path — an actual task failing and being processed through the failure pipeline — remains untested by a live run. The functions work; the end-to-end agent behavior is still unexercised.
**Untested paths:** rebuild path (real failure via Verifier + agent rebuild cycle), research path (tasks/research/ → research-done/)

These remaining untested branches are still likely sources of convention gaps. When a project exercises one, scrutinize carefully.

## Curation Discipline Note (2026-02-25)

KNOWLEDGE.md had two stale entries when I first ran: GC pass count (3 → 4) and Human-Action-Needed observation display behavior. Both caused by verified tasks not being reflected in shared memory. Lesson: always cross-check `tasks/verified/` against KNOWLEDGE.md scope — don't assume all completed work is already captured.

## Curation Heuristics

- Don't add to KNOWLEDGE.md when work only *confirms* existing conventions. Only add when new conventions are *established*.
- Don't write learnings for things already captured in KNOWLEDGE.md or existing learnings/. Check first.
- Don't propose skills for patterns that occurred once. Two or more projects hitting the same friction = skill candidate.
- Trivial pipeline tests (hello-world style) don't produce skills or learnings beyond their first run.

## Proposed Skills Queue

(empty — no pending reviews)
