# Outcome

`human-action-report` is built and in `tasks/review/`. Here is what was implemented:

**`factory needs [--resolve ID] [--all]`** — new CLI command in `runtime/factory_runtime/cli.py`:
- Reads `memory/*/needs.md` across all agent directories, parses entries by `## {id}` heading, groups open items by category (permission-change → config-edit → manual-intervention → approval), sorts oldest-first within each group
- `--resolve ID` — changes `status: open` → `status: resolved`, inserts `resolved_at` timestamp, commits with message `"Resolve factory need: {id}"`. Exits 1 if no open entry found
- `--all` — includes resolved entries with `[resolved]` status tag
- All-clear message when nothing is open

**`memory/builder/needs.md`** — existing reviewer `agents.yaml` blocker documented with exact YAML stanza for human to add manually

**`skills/proposed/human-action-needed/SKILL.md`** — 56-line skill teaching all agents when/how to write needs entries (under 100-line ceiling)

**`skills/reviewer/review-protocol/SKILL.md`** — Step 1.5 added: reviewer reads `memory/*/needs.md` each cycle and flags entries older than 2× heartbeat as escalated items
