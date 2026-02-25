# Librarian — Private Memory

## Pipeline Validation State (as of 2026-02-25)

**Tested path:** spec → build → verify (happy path, no ambiguities, 10/10 score — hello-world-python)
**Factory internal specs also verified:** multi-cli-backend-support (9/10), no-ephemeral-suggestions (9/10)
**Untested paths:** hard gate (tasks/decisions/), rebuild path (tasks/failed/ → rebuild), research path (tasks/research/ → research-done/)

These untested branches are the most likely sources of convention gaps. When a project exercises one, scrutinize carefully — existing KNOWLEDGE.md conventions may be aspirational for those paths rather than confirmed.

## Curation Discipline Note (2026-02-25)

KNOWLEDGE.md had two stale entries when I first ran: GC pass count (3 → 4) and Human-Action-Needed observation display behavior. Both caused by verified tasks not being reflected in shared memory. Lesson: always cross-check `tasks/verified/` against KNOWLEDGE.md scope — don't assume all completed work is already captured.

## Curation Heuristics

- Don't add to KNOWLEDGE.md when work only *confirms* existing conventions. Only add when new conventions are *established*.
- Don't write learnings for things already captured in KNOWLEDGE.md or existing learnings/. Check first.
- Don't propose skills for patterns that occurred once. Two or more projects hitting the same friction = skill candidate.
- Trivial pipeline tests (hello-world style) don't produce skills or learnings beyond their first run.

## Proposed Skills Queue

(empty — no pending reviews)
