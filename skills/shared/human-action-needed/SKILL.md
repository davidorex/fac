---
name: human-action-needed
description: When and how to write a human-action-needed entry to memory/{agent}/needs.md. Agents write these entries when they hit blockers that only a human can resolve.
---

## When to Write a Needs Entry

Write a needs entry when you encounter a blocker that:
- Requires modifying a READ-ONLY file (`agents.yaml`, files in `universe/`)
- Requires an access scope change (new `can_write` or `can_read` in `agents.yaml`)
- Requires a manual human action outside the pipeline (delete files, set up external service, approve a destructive operation)
- Cannot be worked around by existing runtime mechanisms (`factory cleanup-specs`, `factory rebuild`, `factory resolve`)

Write an `observation` entry (non-blocking) during **any work** — not only reflection passes — when you notice friction, limitations, tooling gaps, architectural issues, or improvement opportunities. Observations in your response text are ephemeral; writing them to `needs.md` makes them durable and actionable by the factory.

Do NOT write a needs entry for:
- Routine pipeline work another agent handles (write a research request or spec instead)
- Issues you can resolve through the normal pipeline
- Problems you document as learnings (learnings are lessons, not requests)

## Entry Format

Write to `memory/{your-agent-name}/needs.md`. Entries are appended; the file is never deleted:

```markdown
## {agent}-{kebab-case-description}
- status: open
- created: {ISO 8601 timestamp}
- category: {permission-change | config-edit | manual-intervention | approval | observation}
- blocked: {what you cannot do, or what friction you observe}
- context: {which task, which run, what was attempted}

### Exact Change
{the literal text, YAML block, command, step, or suggested improvement the human needs to review}
```

## Deduplication

Before writing, check your own `memory/{agent}/needs.md` for an existing open entry with the same `{id}` heading. If one exists with `status: open`, do not create a duplicate. If it exists with `status: resolved`, a new occurrence is a new entry — append it.

## Categories

| Category | Use when |
|---|---|
| `permission-change` | Agent's `can_read` or `can_write` needs expansion |
| `config-edit` | A READ-ONLY config file needs modification |
| `manual-intervention` | One-time human action outside the codebase |
| `approval` | Proposed action requires human sign-off before proceeding |
| `observation` | Non-blocking feedback — kernel automatically promotes to `specs/factory-internal/` for structured triage. |

## After Writing

Note the needs entry in your daily log. The human runs `factory needs` to see all open blocker entries and `factory needs --resolve {id}` after taking action.

Observations are automatically promoted to `specs/factory-internal/` by the kernel post-run pass and triaged by the operator via `factory triage`. They no longer appear in `factory needs` output — use `factory triage --list` to review them.
