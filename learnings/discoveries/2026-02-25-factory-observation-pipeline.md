# Discovery: Observation Pipeline — From Dead-End to Structured Lifecycle

**Date:** 2026-02-25
**Project:** factory (no-ephemeral-suggestions spec)
**Agent:** Librarian (post-run curation)

## What Changed

Prior to this change, `category: observation` entries in `memory/{agent}/needs.md` were a dead end. Agents wrote them; `factory needs` surfaced them in a separate section; nothing else happened. Observations required operator manual action to convert into specs. In practice, they were frequently read and forgotten.

The no-ephemeral-suggestions spec replaced this dead end with a kernel-driven promotion pipeline. Observations now flow: `needs.md` → `specs/factory-internal/` (auto-promoted by kernel post-run) → `specs/inbox/` (operator-promoted via `factory triage`) → full spec lifecycle.

## What Was Learned

**Structured lifecycle > surfacing alone.** Showing something to an operator is not enough. Observations need a place to live, a state model (open/promoted/dismissed), severity classification, and a one-command path to the spec pipeline. Without structure, visibility degrades into noise.

**Kernel promotion removes the gap between observation and action.** If agents must rely on operators to manually triage prose entries, observations will accumulate faster than they're processed. Auto-promotion shifts the gap: kernel handles extraction, operator handles triage (a smaller, more structured job).

**Fallback extraction creates data quality risk.** The kernel's `extract_surfaced_observations()` parses agent prose for signal phrases. The `_extract_needs_observation()` fallback path (for non-standard needs.md entries) truncates body text at 300 characters. This affects entries that don't use the standard `blocked:` field format. Going forward, agents using the standard format will not encounter this truncation. Legacy entries lose fidelity, but the full source text is preserved in the original needs.md.

**Four GC passes now, not three.** `cleanup-factory-internal` joins `cleanup-specs`, `cleanup-tasks`, `cleanup-research` as post-execution passes. If you're reading code or docs that say "three cleanup passes," that's outdated.

## Implications

The factory's self-improvement loop tightened: observations that previously required operator awareness now automatically surface in `factory status` with severity and reach the spec pipeline with one command. This is the correct architecture for a system expected to generate many observations over time.
