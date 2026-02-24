# Review: agent-reflection-pass

spec_archive: specs/archive/agent-reflection-pass.md
built: 2026-02-24T19:45:00

## Summary

Implemented `factory reflect [agent-name]` CLI command and extended the `factory needs` command with `--blockers-only` flag and separate `observation` category display.

## Deliverables

### runtime/factory_runtime/cli.py

- Added `import yaml` to module imports (needed for `_agent_yaml_block`)
- Added `PIPELINE_ORDER` constant: `[researcher, spec, builder, verifier, librarian, operator, reviewer]`
- Added `_snapshot_needs_ids(workspace)` — returns set of all entry IDs across memory/*/needs.md; used by reflect for before/after delta counting
- Added `_agent_yaml_block(workspace, agent_name)` — re-reads agents.yaml, serializes the named agent's config block back to YAML text for inclusion in the reflection prompt
- Added `factory reflect [AGENT]` command — sequential per-agent reflection invocation with reflection prompt containing the agent's own YAML config block and inline agent-reflection skill content; counts new needs entries written during pass; summarizes with agent counts and failure detail; exits 1 for unknown agent, 2 if all failed
- Updated `factory needs` — added `--blockers-only` flag; extracted `_print_entry` as local helper; observation entries (category: observation) now displayed in a separate "Observations (N):" section below blocker categories; `--blockers-only` suppresses that section

### skills/proposed/agent-reflection/SKILL.md

57-line skill covering: what to examine during a reflection pass (role, skills, access scopes, daily logs, private memory, pipeline I/O, learnings directory); how to write observations (format, deduplication, blocker vs. observation distinction); what NOT to do.

### skills/proposed/human-action-needed/SKILL.md

Updated version of the shared skill, adding `observation` to the categories table and adding one sentence to "When to Write" noting that observations are written during reflection passes.

## Verification Notes

- `factory reflect nonexistent` → exit 1, prints "Unknown agent: nonexistent" ✓
- `_snapshot_needs_ids` returns set of IDs; delta after reflection = new observations written ✓
- `_agent_yaml_block('builder')` produces clean YAML block ✓
- `factory needs` shows observations in separate section when category: observation present ✓
- `factory needs --blockers-only` suppresses observation section ✓
- `factory reflect --help` shows correct docstring ✓

## Known Behavior Note

When `--blockers-only` is set and all open entries are observations (zero blockers), the header still reads "N open items" but no entries are shown below. The count is factually correct — there ARE open items — but the display may appear inconsistent. This is within spec (spec says to exclude observations, not to adjust the header count). Verifier may judge whether the count should be filtered when --blockers-only is set.

## Proposed Skills Pending Librarian Review

- `skills/proposed/agent-reflection/SKILL.md` — new skill for reflection pass behavior
- `skills/proposed/human-action-needed/SKILL.md` — updated with observation category (replaces existing shared/human-action-needed if Librarian approves)
