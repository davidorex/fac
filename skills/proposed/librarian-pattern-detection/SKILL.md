---
name: pattern-detection
description: How to spot recurring patterns across projects. If Builder hits the same snag in multiple projects, that's a pattern worth writing a skill for.
---

## What Counts as a Pattern

A pattern is a recurring situation — not a one-off event. Before writing a skill,
confirm that the pattern has appeared in at least 2-3 independent contexts.

Signals that something is a pattern:
- The same class of failure appears in `learnings/failures/` more than once
- Builder's daily logs mention the same difficulty across different projects
- Multiple proposed skills address the same underlying situation

One occurrence is an incident. Two occurrences is a coincidence. Three is a pattern
worth systematizing.

## Where to Look

On each heartbeat, scan:
- `learnings/failures/` — failure classes, not just task names
- `learnings/corrections/` — human corrections often reveal systematic gaps
- `memory/daily/builder/` — Builder's recent struggles
- `skills/proposed/` — check whether proposed skills address a common theme

Look for the underlying class, not the surface symptom. "Builder used the wrong
argparse API" and "Builder didn't validate empty inputs" may both be instances of
"Builder lacks Python stdlib idioms" — that's one pattern, not two.

## Writing a Pattern Skill

When a pattern is confirmed, write a skill to `skills/proposed/{scope}-{name}/SKILL.md`
that:
- Names the pattern clearly in the description
- States when the pattern applies (not too broad, not too narrow)
- Gives concrete behavioral guidance, not vague principles
- Stays under 40 lines of content — if it's longer, split it

After writing the proposed skill, note it in your daily log and in `memory/shared/KNOWLEDGE.md`.

## Avoiding Over-Generalization

The risk in pattern detection is making patterns too broad. "Write better code" is
not a useful pattern. "Validate CLI arguments before using them, because argparse
does not reject empty strings" is useful.

Test your pattern skill by asking: "Would an agent reading only this skill understand
what to do differently in the specific situation it describes?" If the answer is
vague, narrow the skill.
