# seed-skill-gaps

## Overview

The factory blueprint (`universe/synthesis/factory-blueprint.md`) describes a minimum seed set of skills for each agent. Of the 20 agent-specific seed skills referenced in `agents.yaml`'s `available` lists, only 6 have SKILL.md content. The remaining 14 are empty directories or don't exist. Agents that load their `available` skills receive no guidance from these missing files, operating with only their first seed skill and the shared skills.

This spec creates the 14 missing seed skills, written to `skills/proposed/` for Librarian review and promotion to the correct agent-specific directories.

## Behavioral Requirements

1. **When Builder executes this spec**, it creates 14 skill files in `skills/proposed/`, one per missing seed skill. Each skill follows the standard SKILL.md format: YAML frontmatter with `name` and `description`, followed by markdown behavioral guidance.

2. **Each skill's content is derived from the blueprint.** The factory blueprint's "Seed Skills in Detail" section and each agent's "Seeded with:" subsection describe the purpose and content of every seed skill. Builder reads these descriptions and produces skill content faithful to them. Where the blueprint provides near-verbatim content (as it does for several skills), the skill should closely mirror it. Where the blueprint provides only a summary, Builder expands it into actionable guidance.

3. **Skills are written to `skills/proposed/` with agent-prefixed naming** so Librarian can identify the target directory: `skills/proposed/{agent}-{skill-name}/SKILL.md`.

## Interface Boundaries

### Skills to create

| # | Agent | Skill Name | Proposed Path | Blueprint Description Summary |
|---|-------|-----------|--------------|------------------------------|
| 1 | researcher | source-evaluation | skills/proposed/researcher-source-evaluation/SKILL.md | How to judge information reliability. Official docs > blogs > SO > training data. Recent > old. Maintained > abandoned. |
| 2 | researcher | recommendation-format | skills/proposed/researcher-recommendation-format/SKILL.md | How to deliver findings as decision-ready briefs. Question, options, recommendation, trade-offs, confidence. Under 500 words. |
| 3 | spec | domain-interview | skills/proposed/spec-domain-interview/SKILL.md | How to interview the human. What questions to ask. When to push for detail vs. when to say "enough, I can spec this." |
| 4 | spec | spec-patterns | skills/proposed/spec-spec-patterns/SKILL.md | Spec templates for common project types: CLI tools, web APIs, data pipelines, libraries, full-stack apps. Skeleton NLSpec structures. |
| 5 | builder | convergence | skills/proposed/builder-convergence/SKILL.md | How to know when you're done. Run tests, check spec. If tests pass and spec satisfied, stop. If 3 iterations on same issue, write failure note and stop. |
| 6 | builder | tool-use | skills/proposed/builder-tool-use/SKILL.md | How to use the filesystem, shell, git. Builder's tool vocabulary and conventions for interacting with the development environment. |
| 7 | verifier | satisfaction-scoring | skills/proposed/verifier-satisfaction-scoring/SKILL.md | The probabilistic satisfaction metric. Not pass/fail — a judgment: "Of N users who wanted what the spec describes, what fraction would be satisfied?" With reasoning. |
| 8 | verifier | scenario-evaluation | skills/proposed/verifier-scenario-evaluation/SKILL.md | How to evaluate against holdout scenarios. Run the scenario mentally or actually. Does the system behave as the scenario expects? |
| 9 | verifier | failure-reporting | skills/proposed/verifier-failure-reporting/SKILL.md | How to write a useful failure report. Not "it's wrong" — what's wrong, why it matters, what the spec says, what the code does, and a suggested fix path. |
| 10 | librarian | pattern-detection | skills/proposed/librarian-pattern-detection/SKILL.md | How to spot recurring patterns across projects. If Builder hits the same snag in multiple projects, that's a pattern — write a skill for it. |
| 11 | librarian | memory-hygiene | skills/proposed/librarian-memory-hygiene/SKILL.md | How to keep memory clean. Archive stale daily logs. Promote important findings to long-term memory. Remove contradictions. |
| 12 | operator | ci-cd | skills/proposed/operator-ci-cd/SKILL.md | How to set up and maintain CI/CD per stack. GitHub Actions patterns, testing configurations, deployment scripts. |
| 13 | operator | dependency-management | skills/proposed/operator-dependency-management/SKILL.md | How to audit, update, and manage dependencies. When to update vs. pin. How to evaluate update safety. |
| 14 | operator | monitoring | skills/proposed/operator-monitoring/SKILL.md | How to check if deployed projects are healthy. What "healthy" means per project type. |

### Skill file format

```markdown
---
name: {skill-name}
description: {one-line description faithful to the blueprint}
---

## {Section heading}
{Behavioral guidance content — 15-40 lines}
```

### Source material

Builder reads the skill descriptions from `universe/synthesis/factory-blueprint.md`, specifically:
- The "Seed Skills in Detail" section for shared skills (reference only — these already exist)
- Each agent's "Seeded with:" subsection for agent-specific skill descriptions

## Constraints

- **Content length: 15-40 lines** of guidance content (excluding YAML frontmatter). The blueprint's own examples are this length. Longer skills are overreaching; shorter skills lack actionable guidance.
- **Behavioral guidance, not tutorials.** Skills tell the agent HOW to approach work and WHAT principles to follow, not step-by-step instructions for specific tools or APIs.
- **Self-contained.** An agent loading a single skill from its `available` list should get useful, standalone guidance. Skills must not require other skills as prerequisites to be meaningful.
- **Faithful to the blueprint.** Skills must encode the behavioral guidance described in the blueprint, not invent new guidance. Where the blueprint is specific (e.g., the source hierarchy in source-evaluation), preserve that specificity.
- **No modifications to existing skills.** Only the 14 missing skills are created. Existing SKILL.md files are untouched.
- **No modifications to `agents.yaml`.** The `available` lists already reference these skill names — only the SKILL.md files are missing.

## Out of Scope

- Promoting skills from `skills/proposed/` to their target agent-specific directories. Librarian handles this on its next heartbeat. (Note: Librarian's `can_write` currently includes `skills/shared/` and `skills/proposed/` but not `skills/{agent}/`. Promoting agent-specific skills may require expanding Librarian's write access — that is a separate concern for the human to address.)
- Creating skills not described in the blueprint. Future skills emerge from the self-improvement loop.
- Evaluating or updating the existing 6 seed skills for quality or completeness.
- Creating the `reviewer/review-protocol` skill (already exists from the self-review-loop implementation).

## Verification Criteria

- After implementation, `skills/proposed/` contains 14 new directories matching the naming convention `{agent}-{skill-name}/`, each containing a `SKILL.md` file.
- Each SKILL.md has valid YAML frontmatter with `name` and `description` fields.
- Each skill's guidance content is 15-40 lines long.
- Each skill's content is faithful to the corresponding description in the factory blueprint.
- No existing skill files (in `skills/shared/`, `skills/{agent}/`, or `skills/reviewer/`) are modified.
- The naming convention `{agent}-{skill-name}` clearly indicates the intended target directory for Librarian routing (e.g., `researcher-source-evaluation` → `skills/researcher/source-evaluation/`).
