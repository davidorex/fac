---
name: self-improvement
description: When you encounter a failure, correction, or new pattern, write a learning and optionally propose a skill.
---

## When to Activate

- A tool call fails unexpectedly
- The human corrects you
- You discover a better approach to something you've done before
- You notice a pattern across multiple tasks
- An external tool or API behaves differently than expected
- You surface friction, limitations, or architectural gaps during any work (not just reflection passes) — these are observations that the factory should know about

## What to Do

1. Write a learning to the appropriate directory:
   - `learnings/failures/{YYYY-MM-DD}-{project}-{summary}.md` for failures
   - `learnings/corrections/{YYYY-MM-DD}-{summary}.md` for human corrections
   - `learnings/discoveries/{YYYY-MM-DD}-{summary}.md` for new patterns

   Include: what happened, what you expected, what actually occurred, what you learned, what should change.

2. If the learning suggests a reusable skill (something that would help ANY agent in similar future situations):
   - Write a SKILL.md to `skills/proposed/{skill-name}/SKILL.md`
   - Librarian will review it on next heartbeat
   - Keep it concise — under 200 lines. If it's longer, it's trying to do too much.

3. If you surface friction, tooling limitations, or architectural gaps during work, write an observation entry to `memory/{your-agent-name}/needs.md` using the `human-action-needed` skill (category: `observation`). This makes the observation durable — prose in your response text is ephemeral and the factory cannot act on it.

4. Update your daily log with a brief note about the learning.

## What NOT to Do

- Don't modify skills in `skills/shared/` directly — always propose via `skills/proposed/`
- Don't write a skill for something that happened once. Wait for patterns (2-3 occurrences).
- Don't write learnings that are just "this didn't work." Always include analysis: WHY it didn't work and what to do differently.
- Don't write a skill that duplicates an existing one. Check `skills/shared/` first.
