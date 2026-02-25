# Verification Report: no-ephemeral-suggestions

spec: specs/archive/no-ephemeral-suggestions.md
reviewed_at: 2026-02-25T09:42:00
verdict: SATISFIED (9/10)

## Summary

The structured observation pipeline replacing the dead-end `category: observation` path is implemented comprehensively. All 14 verification criteria from spec §6 are satisfied. The new `specs/factory-internal/` directory, `factory triage` command, kernel promotion pass, GC integration, skill updates, migration, and pipeline integration (`factory status`, `factory needs`, `factory run`, `factory advance`, `factory reflect`) are all in place and structurally correct.

## Criterion-by-Criterion Assessment

### 1. Kernel safety-net extraction → factory-internal
**PASS.** `extract_surfaced_observations()` writes to `specs/factory-internal/` with correct naming convention `{YYYY-MM-DDTHHMM}-{severity}-{slug}.md`, default severity `low`, format per §6, and `source-type: kernel-extraction`. Signal-phrase scanning, 3-observation cap, and deduplication against agent-written needs are preserved. Output destination changed from needs.md to factory-internal.

### 2. Kernel post-run promotion: needs.md → factory-internal
**PASS.** `promote_needs_observations()` finds `category: observation` + `status: open` entries, creates factory-internal files with `source-type: needs-promotion`, updates needs.md to `status: promoted` with `promoted_to` field. All 3 reviewer observations are correctly promoted. The function handles both `created:` and `filed:` timestamp fields (documented format variation in builder notes).

### 3. Severity heuristics
**PASS.** `_assign_severity()` uses `_CRITICAL_TERMS` and `_HIGH_TERMS` matching the keyword lists in spec §2.4 exactly. NEED-R001 (contains "stale") → high. NEED-R002 (contains "gap") → high. NEED-R003 (body text has no high/critical terms) → low. Classifications are correct.

### 4. Deduplication
**PASS.** `_find_duplicate_factory_internal()` compares normalized whitespace of first 200 characters of `## Observation` text against existing `open` factory-internal files. Matches the spec's text-prefix approach.

### 5. Factory-internal file format
**PASS.** All 3 files follow the exact format from spec §6: `# {slug}`, metadata fields (severity, status, created, source-agent, source-type), `## Observation`, `## Context`. Created timestamps preserve the original observation time for needs-promotion entries.

### 6. `factory triage` — list mode
**PASS.** `factory triage --list` displays open observations sorted by severity (critical → high → low) then age. Shows filename, source agent, age, and first line of observation. `--all` includes promoted and dismissed entries.

### 7. `factory triage` — promote mode
**PASS.** Creates raw intent in `specs/inbox/{slug}.md` with observation text and source metadata. Updates factory-internal file to `status: promoted` with `promoted_to` and `promoted_at`. Git commits the state change.

### 8. `factory triage` — dismiss mode
**PASS.** Requires `--reason`. Updates factory-internal file to `status: dismissed` with `dismissed_reason` and `dismissed_at`. Git commits. Exit code 1 when `--reason` omitted.

### 9. `factory triage` — slug resolution
**PASS.** `_resolve_factory_internal()` accepts full filename or slug substring. Multiple matches → prints all matches and exits code 1. No matches → error message and exits code 1.

### 10. `factory status` — Factory Internal section
**PASS.** Section renders with severity-grouped counts and slug names when open observations exist. Severities with zero items omitted. Entire section omitted when no open observations. Truncation at 3 items per severity with (+N) overflow.

### 11. Next-step hints for critical severity
**PASS.** `_compute_next_actions()` generates `factory triage {filename} --promote` hints for critical-severity items (limited to first 2). High and low observations do not generate hints — correct per spec §2.10.

### 12. Migration
**PASS.** `run_factory_internal_migration()` ran during build, promoted all 3 reviewer observations. `.migrated` sentinel present. Migration is idempotent (skips already-promoted entries). Marker prevents re-running.

### 13. Skill updates
**PASS.** `human-action-needed` SKILL.md: observation category description updated to mention kernel auto-promotion. "After Writing" section notes factory triage path. `self-improvement` SKILL.md: step 3 notes kernel post-run auto-promotion. No changes to agent behavior — informational only, per spec.

### 14. `cleanup-factory-internal` GC pass
**PASS.** Removes promoted files whose `promoted_to` spec is archived. Removes dismissed files older than 30 days. Runs as post-execution pass alongside existing 3 GC passes in `factory run`, `factory advance`. Standalone command `factory cleanup-factory-internal [--dry-run]` available.

### 15. `factory needs` changes
**PASS.** Line 2894 filters out `category: observation` entries. `--blockers-only` retained as backward-compatible no-op. Empty-state message directs operator to `factory triage --list`.

### Post-execution integration
**PASS.** All three dispatch paths (`factory run`, `factory advance`, `factory reflect`) include: (1) observation extraction safety net, (2) needs.md promotion pass, (3) factory-internal GC pass, (4) one-time migration. Ordering is correct: extraction → promotion → GC → migration.

## Minor Observation

The `_extract_needs_observation()` fallback path (for entries without a `blocked:` field) truncates body text at 300 characters. This affects the 3 migrated reviewer entries, which use non-standard format (body paragraph instead of `blocked:` field). NEED-R002's observation text ends mid-word at "A `cleanup-d". The full text is preserved in the original `memory/reviewer/needs.md`. This is a data quality concern in the fallback path — the builder documented the format variation in builder-notes. Going forward, agents using the standard `blocked:` field will not encounter this truncation. The operator can read the full text from the original needs.md entry referenced in the `## Context` section.

## Meta-Scenario Alignment

**Directionally positive.** This change moves the factory closer to the meta-scenario. Observations that previously dead-ended in `memory/*/needs.md` now have a structured lifecycle with operator triage, pipeline promotion, and GC. The operator gains visibility via `factory status` and `factory triage`, and can funnel observations into the spec pipeline with a single command. This increases pipeline autonomy (kernel auto-promotes), improves reliability (nothing stays ephemeral), and reduces required human expertise to interpret observations (structured format with severity classification).

## Satisfaction Score: 9/10

All 14 verification criteria are satisfied. The implementation is comprehensive, well-structured, and correctly integrated across all dispatch paths. The severity heuristics, deduplication, migration, and GC all work as specified. The minor observation (body text truncation in the fallback path) affects only non-standard needs.md entries and does not cause functional failure — the full source text is one reference away. A 10/10 would require the fallback extraction to preserve full text. The gap is small: a meaningful fraction of operators would never notice the truncation, and those who do can trivially find the full text.
