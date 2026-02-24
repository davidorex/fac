---
name: agent-reflection
description: What to examine during a reflection pass and how to write observations to memory/{agent}/needs.md.
---

## When This Skill Activates

When invoked with a reflection prompt (not a heartbeat), follow these instructions rather than the usual heartbeat behavior.

## What to Examine

Read each area before writing. Only write observations where you find genuine friction, misalignment, or improvement opportunities.

**Your role description** — Does it accurately describe what you actually do? Is anything missing or misleading?

**Your skills list** — Which always-loaded skills do you actively use? Which available skills have you never activated? Are skills missing that would help your work?

**Your access scopes** — Have you ever needed to read or write outside your current can_read/can_write? Are there directories in your scopes you never touch?

**Your recent daily logs** — Read the last 5 entries. What patterns emerge? Repeated NO_REPLY? The same workaround appearing multiple times? Recurring blockers?

**Your private memory** — Is it accurate and current? Is anything missing you keep rediscovering?

**Your pipeline inputs** — Are they consistently populated? Is anything stale, malformed, or missing that upstream agents should be producing?

**Your pipeline outputs** — Is your output format working for downstream agents? Have you seen signs it isn't being consumed correctly?

**The learnings directory** — Are there learnings in `learnings/` relevant to your work that haven't been incorporated into your skills or memory?

## How to Write Observations

Use the same format as `shared/human-action-needed` with `category: observation`:

```markdown
## {agent}-{kebab-case-description}
- status: open
- created: {ISO 8601 timestamp}
- category: observation
- blocked: {description of friction, misalignment, or improvement opportunity}
- context: {what prompted this — reflection pass, pattern across runs, specific incident}

### Exact Change
{suggested improvement — may be concrete or a description of what should be different}
```

The `blocked` field for observations describes the friction, not an inability to work. The `### Exact Change` section describes the suggested improvement, even if you're uncertain it's the right fix.

Apply the standard deduplication check: if an open entry with the same ID already exists, do not create a duplicate.

For genuine blockers discovered during reflection, use the appropriate blocker category (`permission-change`, `config-edit`, `manual-intervention`, `approval`) rather than `observation`.

## What NOT to Do

- Do not generate observations about other agents — only your own configuration and experience
- Do not generate specs or intents (that is the reviewer's job)
- Do not reflect on the reflection mechanism itself
- If you have nothing to observe, write NO_REPLY and stop
