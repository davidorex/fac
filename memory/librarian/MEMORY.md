# Librarian — Private Memory

## Factory State

- Factory bootstrapped. All seed skills proposed and promoted (2026-02-24).
- Shared skills: filesystem-conventions, context-discipline, self-improvement, decomposition, human-action-needed, agent-reflection, scenario-authoring-guide
- Factory is operational. 13+ specs through full pipeline. All 6 agents have seed skills.
- `factory reflect` now works with inline skill content (agent-reflection promoted to shared)

## Emerging Patterns (Watching)

### Builder: Dimensional Constraint Deprioritization
- Class: Builder produces high-quality content that exceeds hard dimensional limits in specs
- Observed: `seed-skill-gaps` lineage only — seed-skill-gaps and seed-skill-gaps.v1 are the same spec rebuilt, not independent contexts. This is 1 task family with 2 failed attempts, not 2 independent occurrences.
- Status: Watching — next confirmation must come from a different project or spec to count as independent evidence
- When confirmed (across independent contexts): write a `builder-constraint-handling` skill

## Conventions Established

- Agent-specific skills placed in `skills/{agent}/` not `skills/shared/`
- `skills/shared/` is reserved for cross-agent skills only
- The 40-line limit in `pattern-detection` applies to pattern skills specifically, not all skills
- `memory-hygiene` deficiency: checking "no contradictions" on a sparse KNOWLEDGE.md is insufficient — must also check for omissions by surveying specs/archive/ and tasks/verified/ for conventions not yet reflected

## Known Gaps

- Proposed skill originals in `skills/proposed/` are not deleted after promotion (no shell access). They persist as harmless duplicates. Operator cleanup needed.
- `skills/proposed/` stale files: scenario-authoring-guide, verification-with-scenarios, agent-reflection, human-action-needed — all promoted as of 20:49.
