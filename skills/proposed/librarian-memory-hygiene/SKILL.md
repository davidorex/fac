---
name: memory-hygiene
description: How to keep memory clean. Archive stale daily logs. Promote important findings to long-term memory. Remove contradictions.
---

## Daily Log Maintenance

Daily logs in `memory/daily/{agent}/` are append-only during the day. Librarian's
job is to prevent them from becoming a graveyard of stale entries.

On each heartbeat:
- Scan daily logs older than 7 days
- If a daily log contains findings that have not been promoted to long-term memory,
  promote them now
- If a daily log contains only routine heartbeat notes with no durable learning,
  it can be archived (move to `memory/daily/{agent}/archive/`)
- Never delete daily logs — always archive

A finding worth promoting is one that would change how an agent approaches a future
task. Routine observations are not worth promoting.

## Long-term Memory Promotion

`memory/{agent}/MEMORY.md` is the agent's curated, durable memory. Promote to it:
- Conventions established for the factory or a project
- Decisions made and their rationale
- Patterns confirmed across multiple observations
- Key constraints (e.g., "agents.yaml is human-only, never modify it")

Do NOT promote:
- Task-specific details that won't apply to future tasks
- Observations that are already in `memory/shared/KNOWLEDGE.md`
- Tentative ideas that haven't been validated

## Contradiction Detection

When reviewing `memory/shared/KNOWLEDGE.md` or individual agent memories, watch for:
- Two entries that describe the same convention differently
- A newer entry that supersedes an older one without noting the change
- Agent-specific memories that conflict with shared knowledge

When a contradiction is found, resolve it by:
1. Determining which version is more recent and more authoritative
2. Updating the memory to reflect the correct version
3. Noting the resolution in your daily log

## Skill Review

When reviewing proposed skills in `skills/proposed/`:
- Check against existing skills in `skills/shared/` and `skills/{agent}/` for redundancy
- Verify the skill is actionable — not just descriptive
- Confirm the scope (shared vs. agent-specific) is appropriate
- Do not promote skills that duplicate existing ones — note the duplication to the proposing agent's memory
