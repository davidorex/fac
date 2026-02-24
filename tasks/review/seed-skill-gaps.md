# Review Task: seed-skill-gaps

spec_archive: specs/archive/seed-skill-gaps.md
built_at: 2026-02-24T11:43:44
built_by: builder

## Deliverables

14 new SKILL.md files in `skills/proposed/`, each following the `{agent}-{skill-name}` naming convention:

| # | Path | Agent Target |
|---|------|-------------|
| 1 | skills/proposed/researcher-source-evaluation/SKILL.md | skills/researcher/source-evaluation/ |
| 2 | skills/proposed/researcher-recommendation-format/SKILL.md | skills/researcher/recommendation-format/ |
| 3 | skills/proposed/spec-domain-interview/SKILL.md | skills/spec/domain-interview/ |
| 4 | skills/proposed/spec-spec-patterns/SKILL.md | skills/spec/spec-patterns/ |
| 5 | skills/proposed/builder-convergence/SKILL.md | skills/builder/convergence/ |
| 6 | skills/proposed/builder-tool-use/SKILL.md | skills/builder/tool-use/ |
| 7 | skills/proposed/verifier-satisfaction-scoring/SKILL.md | skills/verifier/satisfaction-scoring/ |
| 8 | skills/proposed/verifier-scenario-evaluation/SKILL.md | skills/verifier/scenario-evaluation/ |
| 9 | skills/proposed/verifier-failure-reporting/SKILL.md | skills/verifier/failure-reporting/ |
| 10 | skills/proposed/librarian-pattern-detection/SKILL.md | skills/librarian/pattern-detection/ |
| 11 | skills/proposed/librarian-memory-hygiene/SKILL.md | skills/librarian/memory-hygiene/ |
| 12 | skills/proposed/operator-ci-cd/SKILL.md | skills/operator/ci-cd/ |
| 13 | skills/proposed/operator-dependency-management/SKILL.md | skills/operator/dependency-management/ |
| 14 | skills/proposed/operator-monitoring/SKILL.md | skills/operator/monitoring/ |

## Verification Criteria (from spec)

- `skills/proposed/` contains 14 new directories matching `{agent}-{skill-name}/`, each with a `SKILL.md`
- Each SKILL.md has valid YAML frontmatter with `name` and `description` fields
- Each skill's guidance content is 15-40 lines long
- Each skill's content is faithful to the corresponding description in `universe/synthesis/factory-blueprint.md`
- No existing skill files in `skills/shared/`, `skills/{agent}/`, or `skills/reviewer/` were modified
- The naming convention clearly indicates the intended target directory for Librarian routing
