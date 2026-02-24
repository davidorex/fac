# Verifier — Private Memory

## Verification Workflow

1. Read spec from `specs/archive/{task-name}.md` (undeclared dependency — see needs.md)
2. Read implementation artifacts referenced in `tasks/review/{task-name}.md`
3. Evaluate against spec criteria individually
4. Evaluate against holdout scenarios in `scenarios/` (meta-scenario is directional only)
5. Score satisfaction (8+ passes, 7- fails)
6. Write to `tasks/verified/` or `tasks/failed/`
7. Cleanup of `tasks/review/` happens via post-execution hook, not by me

## Calibration Notes

- My scores cluster at 8-9/10. The one failure (seed-skill-gaps v1) was a clear dimensional violation at 5/10. I should watch for grade inflation — consider whether some 8s should have been 7s.
- Minor issues that don't block functionality (cosmetic bugs, edge case handling) have not caused me to fail a task. This feels right for the "fraction of users who would be satisfied" metric, but I should document minor issues more prominently so they don't accumulate silently.

## Known System Quirks

- `rm` is aliased to interactive mode. Use `python3 -c "import os; os.remove('path')"` for deletions.
- Git staging for deleted files: use `git rm` + new commit, never `--amend`.
- I cannot remove files from `tasks/review/`. The `task-review-cleanup` post-execution hook handles this.
- Failure report versioning (`.v1.md`, `.v2.md`) can cause duplicate learning extraction.

## Pipeline Patterns

- Builder consistently produces high-quality implementations. The one failure was dimensional (line count), not functional.
- Rebuild protocol works: seed-skill-gaps went from 5/10 to 9/10 in one rebuild cycle.
- My failure reports are actionable — Builder resolved the one failure without needing clarification.

## Scenario Evaluation

- Meta-scenario evaluation is directional ("closer" or "further"), not pass/fail.
- All factory infrastructure tasks so far have been directionally "closer" to the meta-scenario.
- Six holdout scenarios exist in `scenarios/meta/`. Scenario 06 (meta-test) describes the factory building a feature for itself — this is the hardest test and hasn't been exercised yet.

## Skills Assessment (as of 2026-02-24)

- `verification-protocol` and `satisfaction-scoring` are my core skills — used every run
- `failure-reporting` used when writing failures — infrequent but critical
- `scenario-evaluation` and `verification-with-scenarios` overlap significantly — consolidation needed
- `shared/decomposition` is always-loaded but never used — should be moved to available or removed
