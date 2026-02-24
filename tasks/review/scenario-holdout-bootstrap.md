# Review Task: scenario-holdout-bootstrap

spec_archive: specs/archive/scenario-holdout-bootstrap.md
built_by: builder
built_at: 2026-02-24T18:34:48

## What Was Built

CLI scaffolding for the scenario holdout system. No project code artifact — this
is factory infrastructure extending `runtime/factory_runtime/cli.py`.

## Deliverables

### runtime/factory_runtime/cli.py — additions

**Module-level constants (hardcoded, no universe/ dependency at runtime):**
- `_META_SCENARIO_CONTENT` — the factory meta-scenario text verbatim from spec
- `_SCENARIO_TEMPLATE_CONTENT` — the per-project scenario template
- `_SCENARIO_PROJECT_NAME_RE` — regex `[a-z0-9][a-z0-9_-]*` for name validation

**Pure-logic functions:**
- `check_scenario_warning(workspace)` → `str | None` — returns warning when
  `scenarios/meta/factory-itself.md` absent; None otherwise
- `_scenario_coverage(workspace)` → dict — computes directories, total_files,
  meta_exists, warn for `factory status`

**`factory scenario` command group** with three subcommands:
- `factory scenario init-meta` — creates `scenarios/meta/factory-itself.md`;
  idempotent (prints "Already exists:" if present, no modification)
- `factory scenario new <project-name>` — validates name, creates
  `scenarios/{name}/_template.md`; idempotent on existing dir+template
- `factory scenario list` — Rich table: Name (with `[meta]` label), Scenarios,
  Satisfaction columns; help message when empty

**`factory status`** — appended "Scenario Coverage" section showing directory
count, file count, meta-scenario presence, and warning when tasks exist but
meta is absent.

**`factory run` (verifier path)** — pre-verification warning emitted before
`run_agent()` when `scenarios/meta/factory-itself.md` is absent. Informational
only — does not block invocation.

### skills/proposed/scenario-authoring-guide/SKILL.md (39 lines)

Guidance for the human on when/how to write holdout scenarios. Covers timing
(before/alongside spec), quantity (2–5), perspective (user not developer),
focus areas (non-obvious edge cases), holdout rule, and meta-scenario use.

### skills/proposed/verification-with-scenarios/SKILL.md (40 lines)

Guidance for Verifier on integrating scenario evaluation into reports. Covers
`## Scenario Evaluation` section placement, per-scenario evaluation format,
no-scenario fallback, scoring contribution, and directional meta-scenario
evaluation.

### scenarios/meta/factory-itself.md

Created by `factory scenario init-meta` during smoke testing. Contains the
verbatim meta-scenario text from the spec.

## Smoke Test Results

- `factory scenario init-meta` → "Created scenarios/meta/factory-itself.md"
- `factory scenario init-meta` (again) → "Already exists: scenarios/meta/factory-itself.md" (no modification)
- `factory scenario new test-project` → "Created scenarios/test-project/_template.md"
- `factory scenario new test-project` (again) → "Already exists: scenarios/test-project/" (exit 0)
- `factory scenario new INVALID!NAME` → error + exit 1
- `factory scenario list` → table with "meta [meta]" row (count=7), "test-project" row (count=0)
- `factory status` tail → "Scenario Coverage" section with directories:2, files:7, Meta-scenario:✓
- test-project cleaned up after smoke test

## Constraints Respected

- Builder did NOT read scenarios/ to verify meta-scenario content — wrote it,
  did not read it back. Verifier handles content verification.
- Meta-scenario text is hardcoded in `_META_SCENARIO_CONTENT` — no universe/
  dependency at runtime.
- Both proposed skills are ≤40 lines (authoring: 39, verification: 40).
- Pre-verification warning is informational — no blocking or flow alteration.

## Known State

`tasks/building/` shows `human-action-report.md` — this was placed there by a
prior run and appears to be a leftover artifact from that build cycle. It does
not affect this task.
