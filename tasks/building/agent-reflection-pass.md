# Building: agent-reflection-pass

spec_archive: specs/archive/agent-reflection-pass.md
started: 2026-02-24T19:44:00

## Plan

1. Update `_CATEGORY_DISPLAY_ORDER` handling and add `--blockers-only` to `factory needs`
2. Add `PIPELINE_ORDER`, `_snapshot_needs_ids`, `_agent_yaml_block` helpers to cli.py
3. Add `factory reflect [agent-name]` command to cli.py
4. Create `skills/proposed/agent-reflection/SKILL.md`
5. Create `skills/proposed/human-action-needed/SKILL.md` with observation category added
6. Move stale `tasks/building/human-action-report.md` (completed task, artifact is in review)
7. Write review task and commit
