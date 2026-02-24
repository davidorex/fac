# human-action-report

## Overview

Agents encounter blockers that require human intervention — `agents.yaml` is READ-ONLY, permission scopes prevent cleanup, some fixes require manual steps. When this happens, each agent documents the blocker in its own output (failure reports, memory notes, daily logs, verifier assessments), but there is no unified mechanism for surfacing these to the human. The human must dig through scattered locations across multiple agents' outputs to discover what the factory actually needs.

This spec adds a structured convention for agents to declare human-action-needed entries, a runtime aggregation command (`factory needs`) that presents all pending requests grouped by type and priority, and a resolution mechanism (`factory needs --resolve`) that marks entries as addressed.

## Behavioral Requirements

### Agent-side: writing needs entries

1. **Each agent writes human-action-needed entries to `memory/{agent}/needs.md`.** Every agent already has write access to `memory/{agent}/`. No `agents.yaml` changes are required.

2. **Each entry in `needs.md` follows this format:**
   ```markdown
   ## {id}
   - status: open
   - created: {ISO 8601 timestamp}
   - category: {one of: permission-change, config-edit, manual-intervention, approval}
   - blocked: {what the agent cannot do because of this}
   - context: {why this came up — which task, which run, what was attempted}

   ### Exact Change
   {the literal text, YAML block, command, or step the human needs to execute}
   ```
   The `{id}` is a unique slug: `{agent}-{kebab-case-description}` (e.g., `verifier-review-dir-delete-access`, `builder-reviewer-agents-yaml`).

3. **An agent writes a needs entry when it encounters a blocker that:**
   - Requires modification of a READ-ONLY file (`agents.yaml`, files in `universe/`)
   - Requires an access scope change (new `can_write` or `can_read` entry)
   - Requires a manual human action outside the pipeline (e.g., external service setup, approval of a destructive operation)
   - Cannot be worked around by existing runtime mechanisms (cleanup commands, rebuild, resolve)

4. **An agent does NOT write a needs entry for:**
   - Routine pipeline work that another agent handles
   - Issues it can resolve through research requests or spec drafting
   - Problems it documents as learnings (learnings are lessons, not requests)

5. **If an agent encounters the same blocker it has already written a needs entry for, it does not create a duplicate.** The agent checks its own `needs.md` for an existing open entry with the same `{id}` before writing.

### Runtime: the `factory needs` command

6. **`factory needs` reads `memory/*/needs.md` across all agent directories**, parses all entries, filters to `status: open`, and displays them grouped by category. Within each category, entries are sorted oldest-first (longest-waiting gets attention first).

7. **Display format for `factory needs`:**
   ```
   Factory Needs — 5 open items

   Permission Changes (2):
     verifier-review-dir-delete-access    [verifier, 2d ago]
       Verifier cannot delete stale files from tasks/review/
     librarian-agent-skill-dirs           [librarian, 1d ago]
       Librarian's can_write doesn't cover skills/{agent}/ directories

   Config Edits (1):
     builder-reviewer-agents-yaml         [builder, 3d ago]
       Reviewer agent definition needed in agents.yaml

   Manual Interventions (2):
     spec-inbox-stale-cleanup             [spec, 2d ago]
       3 stale files in specs/inbox/ need manual deletion
     operator-ci-github-token             [operator, 4h ago]
       GitHub Actions token expired for project foo
   ```
   Each line shows the entry ID, the requesting agent, the age of the request, and a one-line summary derived from the `blocked` field.

8. **`factory needs --resolve {id}` marks an entry as resolved.** The runtime locates the entry across all `memory/*/needs.md` files by matching the `## {id}` heading, changes `status: open` to `status: resolved`, and appends `- resolved_at: {ISO 8601 timestamp}` to the entry's metadata. The runtime commits the change to git with a message: `"Resolve factory need: {id}"`.

9. **`factory needs --resolve {id}` exits with code 1 and prints an error if no open entry with that ID exists** across any agent's `needs.md`.

10. **`factory needs` with no open items prints:** `Factory needs nothing — all clear.`

### Reviewer integration

11. **The reviewer agent, during its review cycle, checks for unresolved needs entries by reading `memory/*/needs.md`.** If any open entries have been pending for more than 2 review cycles (i.e., `created` timestamp is more than 2x the reviewer's heartbeat interval before the current time), the reviewer notes them in its review output as escalated items. This is a behavioral convention for the reviewer agent, not a runtime enforcement — the reviewer's review-protocol skill should incorporate this check.

### Proposed shared skill

12. **Builder produces a proposed skill at `skills/proposed/human-action-needed/SKILL.md`** that teaches all agents when and how to write needs entries. The skill covers: the trigger conditions (requirement 3), the non-trigger conditions (requirement 4), the entry format (requirement 2), and the deduplication check (requirement 5). Librarian promotes it to `skills/shared/` on review.

## Interface Boundaries

### File: `memory/{agent}/needs.md`

One file per agent. Contains zero or more entries in the format described in requirement 2. The file may contain both open and resolved entries. Entries are appended; the file is append-only except for resolution status updates (which modify in-place).

Example:
```markdown
## spec-inbox-stale-cleanup
- status: resolved
- created: 2026-02-24T10:30:00
- resolved_at: 2026-02-24T14:00:00
- category: manual-intervention
- blocked: Cannot delete stale files from specs/inbox/ — write access only allows creating new files, not removing old ones
- context: pipeline-next-step.md and self-review-loop.md remain in inbox after being archived

### Exact Change
Delete these files manually:
- specs/inbox/pipeline-next-step.md
- specs/inbox/self-review-loop.md

## spec-cannot-delete-drafting
- status: open
- created: 2026-02-24T11:30:00
- category: permission-change
- blocked: Spec agent cannot delete stale files from specs/drafting/ after promoting to specs/ready/
- context: Every spec cycle leaves a drafting copy behind because spec can_write includes drafting but the access model doesn't distinguish create from delete

### Exact Change
No agents.yaml change needed — this is addressed by the spec-pipeline-cleanup runtime hook. If that hook is not yet implemented, run `factory cleanup-specs` manually.
```

### CLI: `factory needs`

```
factory needs

  Reads memory/*/needs.md across all agent directories.
  Displays open items grouped by category, sorted oldest-first.

  Options:
    --resolve {id}    Mark the entry with this ID as resolved
    --all             Show resolved entries alongside open ones (default: open only)

  Exit codes:
    0   Success (including "nothing to show")
    1   --resolve specified but no open entry found with that ID
```

### Categories

| Category | Meaning |
|----------|---------|
| `permission-change` | An agent's `can_read` or `can_write` in `agents.yaml` needs expansion |
| `config-edit` | A READ-ONLY config file (`agents.yaml`, runtime config) needs modification |
| `manual-intervention` | A one-time human action outside the codebase (delete files, run a command, set up an external service) |
| `approval` | Agent has a proposed action that requires human sign-off before proceeding |

## Constraints

- **No `agents.yaml` changes.** Every agent already has write access to `memory/{agent}/`. The runtime has full filesystem access to read across all agent directories and modify entries for resolution.
- **Entries are never deleted.** Resolution changes `status: open` to `status: resolved` and adds a timestamp. The full history persists for reviewer pattern detection and institutional memory.
- **One `needs.md` per agent.** Not one per entry. Agents that have never encountered a blocker have no `needs.md` file, which is equivalent to zero needs.
- **Entry IDs must be globally unique.** The `{agent}-{slug}` convention achieves this because each agent prefixes its own name. The runtime validates uniqueness at display time and warns if duplicates are found.
- **The `factory needs` command does not modify `agents.yaml` or any other file itself.** It surfaces what agents need; the human makes the changes. The only file it modifies is the agent's `needs.md` when resolving.
- **The runtime does not auto-resolve needs entries based on filesystem changes.** Resolution is explicit — either `factory needs --resolve` or automated detection is out of scope. The human confirms the action was taken.

## Out of Scope

- **Automatic detection that a need has been addressed.** If the human adds a `can_write` entry to `agents.yaml` that satisfies a pending permission-change need, the need is not automatically resolved. The human runs `factory needs --resolve {id}` explicitly. Automatic detection would require the runtime to interpret `agents.yaml` semantics, which is brittle.
- **Priority ranking beyond age-based ordering.** The intent mentions priority ordering. This spec uses age (oldest first) as the sole ordering within categories. A priority field could be added later if needed.
- **Notification or interruption.** `factory needs` is pull-based — the human runs it when they want to check. No push notifications, no blocking of agent runs.
- **Needs entries for cross-agent coordination.** This mechanism is strictly for human-required actions. Agents coordinate through the existing filesystem protocol (research requests, spec pipeline, task pipeline).

## Verification Criteria

- An agent that encounters a READ-ONLY blocker (e.g., needing to add a line to `agents.yaml`) writes a well-formed entry to its own `memory/{agent}/needs.md` with all required fields.
- Running `factory needs` with entries across multiple agents' `needs.md` files displays all open entries, grouped by category, with correct age calculation and one-line summaries.
- Running `factory needs --resolve {id}` on a valid open entry changes its status to `resolved`, adds a `resolved_at` timestamp, and commits to git. The entry no longer appears in the default `factory needs` output but does appear with `--all`.
- Running `factory needs --resolve nonexistent-id` prints an error and exits with code 1.
- Running `factory needs` when no `needs.md` files exist (or all entries are resolved) prints the "all clear" message.
- The proposed `skills/proposed/human-action-needed/SKILL.md` is a well-formed skill under 100 lines that teaches agents when and how to write needs entries.
