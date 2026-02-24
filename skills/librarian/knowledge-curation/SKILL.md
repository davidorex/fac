---
name: knowledge-curation
description: How to review proposed skills, curate shared memory, and detect patterns.
---

## Reviewing Proposed Skills

On every heartbeat, check `skills/proposed/` for pending skill files. This is your primary intake queue — agents propose skills here and depend on you to review and promote them. If `skills/proposed/` has entries, reviewing them is your first priority.

1. Read the proposed SKILL.md
2. Check: Is it general enough? A skill about one specific API endpoint is too narrow. A skill about "how to evaluate REST APIs" is useful.
3. Check: Is it accurate? Does it match what you know and what's in `universe/`?
4. Check: Does it conflict with existing skills in `skills/shared/`?
5. Check: Is it well-written? Could another agent follow it without confusion?

If it passes: move to `skills/shared/`, commit with a note about what was reviewed.
If it needs work: edit it in `skills/proposed/`, leave a note about what changed.
If it's redundant or wrong: delete it, write a brief explanation in `learnings/`.

## Pattern Detection

Scan `learnings/failures/` for recurring themes. If Builder hits the same class of problem 3+ times, that's a pattern. Write a skill for it.

Scan daily logs across agents for repeated workarounds. If agents keep doing the same manual step, that's a skill waiting to be written.

## Memory Hygiene

- Daily logs older than 7 days: scan for anything worth promoting to MEMORY.md or KNOWLEDGE.md, then archive
- KNOWLEDGE.md: check for contradictions, outdated facts, redundancies. But also: if KNOWLEDGE.md is empty or sparse relative to the volume of completed work in `tasks/verified/` and `specs/archive/`, populating it is the priority. Survey verified tasks and archived specs to extract conventions, patterns, and operational facts that belong in shared knowledge. An empty KNOWLEDGE.md with 12 verified tasks means curation hasn't happened yet — not that there's nothing to curate.
- PROJECTS.md: update project statuses based on recent task movements

## Using the Universe

When reviewing skills, cross-reference with `universe/context-engineering/` to ensure proposed skills align with context discipline principles. A proposed skill that encourages loading too much context is harmful regardless of its content.
