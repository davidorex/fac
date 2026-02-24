# Verification Report: failed-task-rebuild-convention

spec: specs/archive/failed-task-rebuild-convention.md
artifact: runtime/factory_runtime/cli.py
reviewed_at: 2026-02-24T12:31Z
verdict: SATISFIED (8/10)

## Summary

The `factory rebuild {task-name}` CLI command is correctly implemented. All structural operations — copying the archived spec to ready, versioning the failure report, writing the rebuild brief with Verifier remediation guidance, git commit — work as specified. Error handling for missing prerequisites and already-in-progress rebuilds is correct. The cleanup integration for stale `.rebuild.md` files is correct. Two minor defects exist: one in score extraction (functional) and one in dry-run display (cosmetic). Neither prevents rebuild from fulfilling its purpose.

## Criterion-by-Criterion Assessment

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| 1 | `specs/ready/{task}.md` exists and matches archive after rebuild | PASS | `shutil.copy2` — exact copy, archive untouched |
| 2 | `specs/ready/{task}.rebuild.md` exists, `## What to Fix` matches `## Path to Resolution` | PASS | Verbatim extraction via `_extract_section` |
| 3 | `tasks/failed/{task}.md` renamed to `.v{N}.md`, original gone | PASS | `Path.rename()`, N incremented correctly |
| 4 | Missing spec/failure report → error, no modifications | PASS | Both files checked before any mutations occur |
| 5 | Spec already in ready → warning, no modifications | PASS | Checked first (exit 2), before prerequisite check |
| 6 | Builder reads `.rebuild.md` companion | DEFERRED | Builder-side behavior, not testable in isolation |
| 7 | Complete cycle works | STRUCTURAL PASS | File paths and state transitions are correct; live Builder run required for full E2E |

## Behavioral Assessment

- **Behavioral correctness**: All CLI behaviors match the spec. Exit codes 0/1/2 are correct. File operations follow the specified order. Rebuild brief format matches the spec template exactly.
- **Boundary correctness**: All error paths tested — missing files, duplicate in ready. Version numbering handles N > 1 correctly (while loop). Fallback chain for missing `## Path to Resolution` works: Summary → full text.
- **Completeness**: All 7 behavioral requirements addressed. Requirements 4-6 (Builder behavior on rebuild) are correctly deferred — they're Builder's responsibility, and the spec acknowledges this.
- **Excess**: None. `_extract_section` is reasonable code reuse, not gold-plating.

## Issues Found

### Issue 1: Score extraction regex mismatches real heading format (functional)

The `_extract_section(failure_text, "## Satisfaction Score")` call expects the heading to be exactly `## Satisfaction Score` followed by whitespace and newline. All existing Verifier failure reports use the format `## Satisfaction Score: N/10` — the score is embedded in the heading text, not in the body below it. The `: N/10` suffix causes the regex to fail, so `_extract_section` returns `None`, and `prior_score` falls through to `"unknown"`.

**Impact**: Every rebuild brief will report `prior_score: unknown` even when the failure report contains a clear score. Builder loses a data point but still receives the full remediation guidance from `## What to Fix`. Non-blocking.

**Fix**: The score extraction should search the full text for `\d+/10` near a `## Satisfaction Score` heading, or parse the heading line itself rather than relying on section-body extraction.

### Issue 2: Dry-run display prefix for rebuild brief cleanup (cosmetic)

The `cleanup-specs` CLI command (line 674) does `line.replace("Cleaned stale spec:", ...)` which only substitutes the "Cleaned stale spec:" prefix. Rebuild brief cleanup lines use "Cleaned stale rebuild brief:" and are not matched by this replacement. In dry-run mode, rebuild brief cleanup lines will display as "Cleaned stale rebuild brief:" instead of "[dry-run] Would clean:".

**Impact**: Display-only. The actual dry-run behavior (suppressing deletion) is correct. Builder self-reported this issue.

## Satisfaction Score: 8/10

Of 10 users who wanted what the spec describes:
- ~8 would be satisfied: the core rebuild workflow — human triggers it, spec returns to ready, failure context is extracted into a rebuild brief for Builder, failure report is versioned — works correctly. The missing score is a minor data loss that doesn't impede Builder's ability to act on the rebuild brief.
- ~2 would notice that the `prior_score` field is always `unknown` despite the score being present in the failure report, and would consider this a gap in the implementation's promise to extract it.

## Path to Resolution

The score extraction in `rebuild_task` should search for `\d+/10` in the full line matching `## Satisfaction Score` rather than relying on `_extract_section`'s body-only extraction. The dry-run display replacement in `cleanup_specs_cmd` should handle both "Cleaned stale spec:" and "Cleaned stale rebuild brief:" prefixes.
