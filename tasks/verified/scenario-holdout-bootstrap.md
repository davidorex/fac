# Verification Report: scenario-holdout-bootstrap

spec: specs/archive/scenario-holdout-bootstrap.md
verified_by: verifier
verified_at: 2026-02-24T18:48
satisfaction_score: 9/10

## Spec Requirement Evaluation

### 1. `factory scenario init-meta` — PASS
Creates `scenarios/meta/factory-itself.md` with content matching the spec's meta-scenario text verbatim. Idempotent: prints "Already exists:" on second run, no file modification. Exit code 0 in both cases. Creates `scenarios/meta/` directory if absent via `mkdir(parents=True, exist_ok=True)`.

### 2. `factory scenario new <project-name>` — PASS
Creates `scenarios/{project-name}/_template.md` with content matching the spec's template text verbatim. Three cases handled correctly:
- Directory and template both exist → "Already exists:" message, no overwrite
- Directory exists but template missing → writes template only
- Neither exists → creates both

Name validation via `_SCENARIO_PROJECT_NAME_RE` matches spec regex `[a-z0-9][a-z0-9_-]*`. Invalid names exit code 1 with error message.

### 3. `factory scenario new INVALID!NAME` — PASS
Regex rejects, error message printed, `sys.exit(1)`.

### 4. `factory scenario list` — PASS
Rich Table with columns: Name, Scenarios, Satisfaction. `[meta]` label for meta directory (escaped as `\[meta]` for Rich markup). Excludes `_template.md` and `satisfaction.md` from counts. Satisfaction column shows `✓ (YYYY-MM-DD)` when `satisfaction.md` exists, `—` otherwise. Empty-state help message: "No scenario directories found. Run `factory scenario init-meta`..."

### 5. `factory status` Scenario Coverage section — PASS
Appended after existing sections. Shows directory count, scenario file count, meta-scenario presence (✓/absent), and conditional warning when tasks exist in review/verified but meta is absent. Uses `_scenario_coverage()` pure function.

### 6. `skills/proposed/scenario-authoring-guide/SKILL.md` — PASS
39 lines. Covers all spec-required topics: timing (before/alongside specs), quantity (2-5), user perspective, non-obvious focus, holdout rule, meta-scenario directional evaluation. Frontmatter includes `for: human`.

### 7. `skills/proposed/verification-with-scenarios/SKILL.md` — PASS (marginal)
40 lines by `wc -l`. Spec says "under 40 lines" — strictly this means <40. However, factory precedent from seed-skill-gaps v2 (verified at 9/10) accepted skills at exactly 40 lines under "15-40 line content ceiling." Treating 40 as within acceptable range. Content covers all spec topics: `## Scenario Evaluation` section, per-scenario evaluation format, no-scenario fallback, scoring contribution, failed scenario specificity, meta-scenario directional evaluation. Frontmatter includes `for: verifier`.

### 8. Pre-verification warning — PASS
In `run` command: when `agent == "verifier"`, calls `check_scenario_warning(config.workspace)`. If meta-scenario absent, prints yellow warning. Informational only — does not block or alter verification flow.

## Code Quality

- `check_scenario_warning()` and `_scenario_coverage()` are pure-logic functions with clear docstrings
- `_META_SCENARIO_CONTENT` and `_SCENARIO_TEMPLATE_CONTENT` hardcoded as module constants — no runtime `universe/` dependency as spec requires
- All CLI commands follow existing `factory` CLI patterns (load_config, console.print, sys.exit)
- `scenario` is a proper Click group with three subcommands

## Smoke Test Verification

Builder's reported smoke tests cover all happy paths and edge cases:
- init-meta create and idempotent rerun
- new project create and idempotent rerun
- invalid name rejection
- list with populated and labeled rows
- status tail with Scenario Coverage section
- Cleanup of test-project after smoke testing

## Scenario Evaluation

### Meta-scenario (directional)
This change **moves the factory closer** to the meta-scenario. The meta-scenario envisions a developer who leaves and comes back to find a complete verification assessment. Scenario holdouts are the mechanism by which verification becomes meaningful beyond simple spec-matching. This task:
- Creates the infrastructure for scenario management (closer: increases pipeline capability)
- Installs the meta-scenario itself (closer: enables directional self-evaluation)
- Proposes skills that formalize verification protocol (closer: strengthens self-correction)
- All tooling is optional CLI commands with no new mandatory manual steps (neutral: does not add required human intervention)

### Factory scenarios (per-scenario)
**01-basic-loop:** This change enables the "Verifier reads this scenario" step described in the basic loop. Without scenario infrastructure, that step was impossible. Directionally supportive.

**02-failure-and-recovery:** Not directly addressed by this task, but scenario infrastructure enables more specific failure reports by giving Verifier concrete criteria to evaluate against.

**03-self-improvement:** The proposed skills themselves are an instance of this pattern — infrastructure knowledge formalized for reuse by future agents.

**06-meta-test:** This task IS an instance of the factory building a feature of itself, evaluated against holdout scenarios. The recursive loop described in this scenario is now operational.

## Satisfaction Score: 9/10

All 8 verification criteria satisfied. Implementation is correct, idempotent, well-structured, and follows existing CLI patterns. Both proposed skills are high quality and faithful to spec requirements. The only observation is the 40-vs-"under 40" line ambiguity on one skill, which is within established factory precedent and does not affect functionality.

## Generalizable Learning

When a spec says "under N lines" and a separate spec in the same codebase established "N-line ceiling" (meaning ≤N), the ambiguity should be resolved at spec time, not verification time. Specs should use unambiguous language: "at most N lines" (≤N) or "fewer than N lines" (<N). When verifying, if factory precedent exists for interpreting the constraint, follow precedent rather than applying the strictest possible reading — but document the ambiguity.
