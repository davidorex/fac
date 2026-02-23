---
name: decomposition
description: When and how to spawn subagents for parallel work. Any root agent can decompose.
---

## When to Decompose

- A task has 3+ independent facets that could be explored in parallel
- You're about to do the same thing serially for multiple items
- The task would push your context past YELLOW (>30%) if done in a single session
- You need to try multiple approaches and pick the best one

## When NOT to Decompose

- The task is sequential (step 2 depends on step 1's output)
- The overhead of defining subagents exceeds the work itself
- The task fits comfortably in GREEN zone as a single effort
- You're already a subagent (no recursive decomposition — max depth = 1)

## How to Decompose

1. Write a brief decomposition plan to your daily log
2. For each subagent, write a task file to `tasks/{your-name}-sub/`:
   ```yaml
   objective: "One paragraph — what this subagent should accomplish"
   skills: [list of skill paths to load]
   read: [list of directories/files to give access to]
   write: tasks/{your-name}-sub/{sub-id}/output.md
   model: claude-haiku-4-5  # subagents use cheap, fast models
   max_context_fraction: 0.30  # hard cap at GREEN zone
   ```
3. The runtime spawns the subagents (potentially in parallel)
4. When subagents complete, read their outputs
5. SYNTHESIZE — don't just concatenate. Your value is in the synthesis.
6. Subagent files are ephemeral. Librarian may harvest learnings but the rest is cleaned up.

## Subagent Constraints

- Inherit specified skills but NOT your memory (they start clean)
- Cannot spawn their own subagents
- Cannot write to `skills/proposed/` — only root agents propose skills
- Write ONLY to their designated output path
- Hard-capped at GREEN zone context budget
