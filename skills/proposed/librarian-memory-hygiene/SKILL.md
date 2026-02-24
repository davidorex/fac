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

## Long-term Memory Promotion

`memory/{agent}/MEMORY.md` is the agent's curated, durable memory. Promote to it:
- Conventions established for the factory or a project
- Decisions made and their rationale
- Patterns confirmed across multiple observations
- Key constraints (e.g., "agents.yaml is human-only, never modify it")

Do NOT promote:
- Task-specific details that won't apply to future tasks
- Observations that are already in `memory/shared/KNOWLEDGE.md`

## Contradiction Detection

When reviewing `memory/shared/KNOWLEDGE.md` or individual agent memories, watch for:
- Two entries that describe the same convention differently
- A newer entry that supersedes an older one without noting the change
- Agent-specific memories that conflict with shared knowledge

When a contradiction is found, determine which version is more authoritative, update to reflect it, and note the resolution in your daily log.

## Skill Review

When reviewing `skills/proposed/`: check for redundancy against existing skills, verify
actionability, and confirm scope. Do not promote duplicates — note the duplication in
the proposing agent's memory.
