# Review: human-action-report

spec_archive: specs/archive/human-action-report.md
built: 2026-02-24T14:13:53

## What Was Built

### 1. `factory needs` CLI command (`runtime/factory_runtime/cli.py`)

Three new pure functions:
- `_format_age(created_str)` — formats ISO 8601 timestamps as human-readable age strings (`Xm ago`, `Xh ago`, `Xd ago`)
- `parse_needs_entries(workspace)` — globs `memory/*/needs.md`, splits each file on `## ` headings, parses all metadata fields, returns list of dicts
- `resolve_need(workspace, entry_id)` — locates an open entry by ID across all needs.md files, changes `status: open` to `status: resolved`, inserts `resolved_at` timestamp, writes file, returns (exit_code, message)

`factory needs [--resolve ID] [--all]` command:
- Default: shows open entries grouped by category (permission-change → config-edit → manual-intervention → approval), sorted oldest-first within each group
- `--all`: includes resolved entries with `[resolved]` tag
- `--resolve ID`: resolves an entry and commits with message `"Resolve factory need: {id}"`, exits 1 if no open entry found
- All-clear message when no open items
- Duplicate ID detection (warn, don't fail)
- Rich markup escaping: `\[agent, age]` and `\[resolved]` brackets escaped to prevent Rich from consuming them as markup tags

### 2. `memory/builder/needs.md`

Contains the existing blocker from the `self-review-loop` build: reviewer agent stanza missing from `agents.yaml` (READ-ONLY). Entry includes the exact YAML stanza the human needs to add.

### 3. `skills/proposed/human-action-needed/SKILL.md`

56-line skill covering: trigger conditions, non-trigger conditions, entry format, category table, deduplication check, and what happens after writing. Under 100-line limit.

### 4. `skills/reviewer/review-protocol/SKILL.md` updated

Added Step 1.5 (Needs Escalation Check) between deduplication check and main review categories. Reviewer reads `memory/*/needs.md` during each cycle and flags entries older than 2× heartbeat interval as escalated items.

## Smoke Tests Run

- `factory needs` → correct display with grouped categories, age, blocked summary
- `factory needs --resolve nonexistent-id` → exit 1, error message
- `factory needs --resolve builder-test-resolve-smoke` (temp entry) → resolved, committed, removed from default view, appears in `--all` with `[resolved]` tag
- `factory needs --all` → shows both open and resolved with status tag
- Empty memory dir → 0 entries, all-clear path confirmed

## Deviations from Spec

None.

## Concerns

None.
