# self-review-loop

## Overview

The factory currently operates as a straight pipeline: the human writes intents, agents process them. No agent examines the factory as a whole — its values, blueprint, learnings, completed work, skill gaps — and asks "what should we build next?" This feature adds a new agent, **reviewer**, whose sole job is to read broadly across the factory's state and generate well-formed intents for improvements it identifies. Generated intents go to `specs/inbox/` where the human curates them like any other intent — approving, modifying, or discarding. The human shifts from sole author of improvement ideas to curator of ideas the factory also generates.

## Behavioral Requirements

1. **When `factory run reviewer` is invoked, the reviewer agent reads the factory's reference documents, source code, agent definitions, shared memory, completed work history, learnings, and skill inventory, then identifies gaps, inconsistencies, unmet values, recurring failure patterns, or logical next steps.**

2. **When the reviewer identifies an actionable improvement, it writes an intent file to `specs/inbox/` following the standard intent format (`## What I'm Seeing` / `## What I Want to See`).** Each intent file is named `{brief-slug}.md` (e.g., `missing-verifier-skills.md`). The filename must not collide with any existing file in `specs/inbox/`, `specs/drafting/`, `specs/ready/`, or `specs/archive/`.

3. **When the reviewer finds no actionable improvements, it responds with NO_REPLY.** No empty or trivial intents are generated.

4. **Each generated intent must cite specific evidence.** The "What I'm Seeing" section must reference concrete files, directory states, learning entries, or value statements — not vague observations. Example: "The `skills/verifier/` directory contains only `.gitkeep` files for `scenario-evaluation` and `failure-reporting` — these skills are listed in agents.yaml but have no content."

5. **The reviewer generates at most 3 intents per run.** If more than 3 improvements are identified, it prioritizes by impact (recurring failure patterns > unmet values > logical next steps > minor gaps) and notes the deprioritized items in its daily log for the next run.

6. **Before generating any intent, the reviewer checks `specs/inbox/`, `specs/drafting/`, `specs/ready/`, and `specs/archive/` for existing work that addresses the same concern.** Duplicate or overlapping intents are not generated. If an existing intent partially addresses the concern, the reviewer notes this in its daily log but does not generate a competing intent.

7. **The reviewer does not modify any existing file outside its own memory and daily log.** It only creates new files in `specs/inbox/`.

## Interface Boundaries

### Agent Definition

The reviewer agent is defined in `agents.yaml` with the following profile:

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

Note: the reviewer intentionally does NOT have `shared/decomposition` in its always-loaded skills. Its job is a single coherent review pass, not parallel research. It also has no access to `projects/` (actual codebases) or `scenarios/` (holdouts) — its scope is the factory's structure and meta-state, not the code it produces.

### Review Categories

The reviewer examines the factory along these dimensions, in priority order:

1. **Failure patterns**: Read `learnings/failures/`. Are there recurring themes (same category of failure appearing 2+ times) that suggest a systemic fix rather than individual patches?

2. **Value alignment**: Read `universe/values.md`. For each value, check whether the factory's current structure and behavior embody it. Where a value is unaddressed or contradicted, that's an intent candidate.

3. **Blueprint gaps**: Read `universe/synthesis/factory-blueprint.md`. Which described capabilities or bootstrap steps are not yet built? Are there features the blueprint envisions that have no corresponding spec, task, or verified work?

4. **Skill coverage**: Scan `skills/{agent}/` directories. Which skills are listed in `agents.yaml` `available` lists but have no corresponding `SKILL.md` content (only `.gitkeep`)? Which agents have been active (have daily logs) but have no agent-specific skills beyond the shared set?

5. **Completed work audit**: Read `specs/archive/` and `tasks/verified/`. What has been built? Are there logical next steps or known follow-ups mentioned in builder notes or verification reports that haven't been initiated?

6. **Memory coherence**: Read `memory/shared/KNOWLEDGE.md` and `memory/shared/PROJECTS.md`. Are there stale entries, missing entries for active work, or contradictions?

### Skill: `reviewer/review-protocol`

Builder should create a skill at `skills/reviewer/review-protocol/SKILL.md` that encodes the review process:

- The review category priority order above
- The evidence-citation requirement for generated intents
- The deduplication check procedure
- The 3-intent-per-run limit and the prioritization criteria
- The format for daily log entries (what was reviewed, what was found, what was generated, what was deferred)

### Workspace Additions

Builder creates these directories:

- `memory/reviewer/` (with `MEMORY.md` initialized)
- `memory/daily/reviewer/`
- `skills/reviewer/` (with `review-protocol/SKILL.md`)

### Intent File Format

Generated intent files follow the existing template in `universe/synthesis/intent-template.md`:

```markdown
# {working-title}

## What I'm Seeing
[Concrete observations with file/directory references]

## What I Want to See
[Desired end state]
```

Each generated intent includes a metadata comment at the top of the file:

```markdown
<!-- generated by: reviewer | run: {YYYY-MM-DD}T{HH:MM} | evidence: {brief citation} -->
```

This metadata line lets the human (and Spec agent) distinguish human-authored intents from reviewer-generated ones, and trace the evidence.

## Constraints

- The reviewer must not generate intents about its own capabilities or existence. Self-referential improvement loops are the human's prerogative.
- The reviewer must not read or reference `scenarios/` or `tasks/building/`. It has the same information isolation as other non-verifier, non-builder agents.
- The reviewer must not propose changes to `agents.yaml` directly. If it identifies a need to change agent configuration, it generates an intent describing the desired change, and the human decides.
- The reviewer must not read `projects/` (actual codebases). Its scope is the factory's meta-structure, not the software the factory produces.
- The 3-intent limit is per-run, not per-category. Even if all 3 are from "failure patterns," that's fine if those are the highest priority.
- The weekly heartbeat is a suggestion. The human can run `factory run reviewer` at any time. The heartbeat just ensures it runs at least once a week without manual invocation.
- No runtime code changes should be needed. The existing runtime loads agents from `agents.yaml` dynamically. Adding a new agent entry and its skills/memory directories should be sufficient.

## Out of Scope

- Automatic processing of reviewer-generated intents. The human curates the inbox. The reviewer generates; the human approves.
- Reviewer modifying existing specs, tasks, or learnings. It is read-only everywhere except `specs/inbox/` and its own memory.
- Cross-project code review. The reviewer examines the factory's structure, not the quality of code in `projects/`.
- Priority scoring or ranking of generated intents beyond the implicit ordering by review category priority.
- Integration with external monitoring, analytics, or dashboards.
- Reviewer generating scenarios for `scenarios/`. That remains the human's domain.

## Verification Criteria

- Running `factory run reviewer` on a factory with empty `skills/verifier/scenario-evaluation/` (only `.gitkeep`) results in an intent file in `specs/inbox/` that references the missing skill content.
- Running `factory run reviewer` when `specs/inbox/` already contains an intent addressing skill gaps produces no duplicate intent for the same gap.
- Running `factory run reviewer` on a factory with no identifiable gaps results in NO_REPLY and no files written to `specs/inbox/`.
- Generated intent files follow the standard format with the metadata comment line.
- No more than 3 intent files are created per run.
- The reviewer's daily log contains an entry describing what was reviewed, what was found, and what was generated or deferred.
- The `agents.yaml` entry, memory directories, and skill file all exist after implementation.
