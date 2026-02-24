# Review: self-review-loop

spec_archive: specs/archive/self-review-loop.md
built_at: 2026-02-24T11:00Z

## What Was Built

### Filesystem Artifacts Created

- `memory/reviewer/MEMORY.md` — initialized with role, access boundaries, operating protocol, review category priority, and intent file format
- `memory/daily/reviewer/.gitkeep` — directory scaffolded for daily logs
- `skills/reviewer/review-protocol/SKILL.md` — full review process skill: deduplication check procedure, all 6 review categories with criteria and intent candidate thresholds, prioritization rubric, intent file format with metadata line, daily log format, evidence requirements, and hard constraints

### Blocked: agents.yaml

The spec's `agents.yaml` entry (Behavioral Requirement 1 + Interface Boundaries → Agent Definition + Verification Criterion: "The `agents.yaml` entry...all exist after implementation") **cannot be implemented**.

The user's global `CLAUDE.md` contains an explicit hard constraint:
> `agents.yaml is READ-ONLY. Never modify agents.yaml.`

This conflicts directly with the spec's requirement to add a `reviewer` entry. I did not modify `agents.yaml`. The human must decide whether to:
1. Add the reviewer entry to agents.yaml manually, or
2. Relax the agents.yaml constraint for new agent additions, or
3. Define a different mechanism for adding new agents

The `agents.yaml` entry the spec prescribes is:

```yaml
reviewer:
  role: "Observe the factory. Identify what's missing, broken, or inconsistent. Generate improvement intents."
  model: claude-sonnet-4-5
  provider: anthropic
  skills:
    always: [shared/filesystem-conventions, shared/context-discipline, shared/self-improvement]
    available: [reviewer/review-protocol]
  memory:
    private: memory/reviewer/MEMORY.md
    daily: memory/daily/reviewer/
  can_read:
    - universe/
    - runtime/
    - agents.yaml
    - specs/
    - tasks/verified/
    - tasks/failed/
    - memory/shared/
    - skills/
    - learnings/
  can_write:
    - specs/inbox/
    - memory/reviewer/
    - memory/daily/reviewer/
    - skills/proposed/
  cannot_access:
    - scenarios/
    - tasks/building/
    - projects/
  heartbeat: "0 6 * * 1"  # weekly, Monday 6am
  shell_access: none
```

## Deviations from Spec

None in what was implemented. All implemented artifacts match the spec exactly. The only deviation is the agents.yaml entry, which is blocked by access control — not a spec quality issue.

## Verification Status

Criteria requiring manual human action (add agents.yaml entry):
- ❌ "The `agents.yaml` entry, memory directories, and skill file all exist after implementation." — agents.yaml entry missing

All other criteria can pass once agents.yaml is updated:
- ✅ memory/reviewer/MEMORY.md initialized
- ✅ memory/daily/reviewer/ exists
- ✅ skills/reviewer/review-protocol/SKILL.md exists with full content
- ✅ Behavioral criteria (1–7) are implementable once the runtime can run `factory run reviewer`
- ✅ Intent file format with metadata comment is encoded in the skill
- ✅ 3-intent limit, deduplication, and NO_REPLY behavior are specified in the skill
