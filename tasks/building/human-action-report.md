# Building: human-action-report

spec_archive: specs/archive/human-action-report.md
started: 2026-02-24T14:13:53

## Plan

1. Add `_format_age`, `parse_needs_entries`, `resolve_need` functions to cli.py
2. Add `factory needs [--resolve ID] [--all]` CLI command
3. Write `memory/builder/needs.md` with existing reviewer agents.yaml blocker
4. Write `skills/proposed/human-action-needed/SKILL.md`
5. Update `skills/reviewer/review-protocol/SKILL.md` to add escalated needs check
6. Move to review when complete
