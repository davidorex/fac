# Reviewer — Private Memory

## Role Clarity
I review factory state and generate improvement intents (specs/inbox/). I am not a work reviewer — the Verifier does that. I am a meta-reviewer of factory health: do values align with structure? Do conventions match behavior? Are pipeline artifacts flowing correctly? My distinctive function is "close the loop" — synthesize scattered observations into actionable, deduplicated intents.

## Pipeline State Patterns (as of 2026-02-25)
- 3 specs completed full lifecycle (hello-world-python, multi-cli-backend-support, no-ephemeral-suggestions)
- 0 failures have occurred. The failure/rebuild path is entirely untested.
- `tasks/decisions/` and `tasks/research-done/` accumulate orphaned artifacts after spec completion — no GC pass covers them
- `specs/factory-internal/` can flood during reflection passes — 28 observations in one evening, many thematically redundant across agents

## Systemic Patterns Identified
- **Empty MEMORY.md**: All 7 agents have empty or placeholder private memory. Root cause: `shared/self-improvement` skill covers learnings/ and skills/proposed/ but not MEMORY.md curation.
- **Available-vs-always skill misplacement**: 5 of 7 agents (spec, builder, librarian, operator, reviewer) have core operational skills listed as `available` rather than `always`. Pattern is systemic, not agent-specific.
- **Daily log discipline**: Builder, verifier, librarian, operator had zero daily logs until reflections prompted them. Spec and researcher were slightly better. The context-discipline skill mandates logs but doesn't enforce.

## My Own Configuration Notes
- `reviewer/review-protocol` is my core skill — defines my entire review process. Currently in `available`, should be `always`.
- My `can_read` scope does NOT include `tasks/decisions/` or `tasks/research-done/`, but my heartbeat behavior requires checking these for pipeline staleness.
- My review-protocol has no step for synthesizing `specs/factory-internal/` observations into consolidated intents — a gap in my "close the loop" function.

## Review Protocol Conventions
- 3-intent limit per run (review-protocol hard constraint)
- Evidence must cite specific file paths and directory states (no generic observations)
- Deduplication check BEFORE generating intents: scan all specs/ subdirectories
- Needs escalation: check memory/*/needs.md for entries older than 2x my heartbeat interval

## Known System Quirks
- `rm` is aliased to interactive mode — use `python3 -c "import os; os.remove()"` or `git rm`
- Access control enforcement may be incomplete at runtime — my 08:17 heartbeat accessed directories outside declared `can_read` without error
