# Task: no-ephemeral-suggestions

## Status
Built and committed.

## What Was Built

Structured observation pipeline replacing the dead-end `category: observation` path in `memory/{agent}/needs.md`.

### New directory
`specs/factory-internal/` — dated, severity-tagged observation files created by the kernel.

### New CLI commands
- `factory triage [--list] [--all]` — list open observations by severity/age
- `factory triage {file|slug} --promote` — write intent to specs/inbox/, mark promoted
- `factory triage {file|slug} --dismiss --reason "..."` — mark dismissed
- `factory triage {file|slug}` — display mode with available actions
- `factory cleanup-factory-internal [--dry-run]` — GC pass (standalone)

### Modified commands
- `factory status` — new "Factory Internal" section with severity-grouped counts
- `factory needs` — observations excluded; --blockers-only retained as no-op
- `factory run` / `factory advance` / `factory reflect` — new post-execution passes

### Kernel functions added
- `promote_needs_observations(workspace, agent)` — per-agent needs.md promotion
- `run_factory_internal_migration(workspace)` — one-time cross-agent migration
- `cleanup_factory_internal(workspace, dry_run)` — lifecycle GC pass
- `extract_surfaced_observations()` — output changed to specs/factory-internal/

### Skill updates
- `skills/shared/human-action-needed/SKILL.md` — observation category + After Writing
- `skills/shared/self-improvement/SKILL.md` — step 3 notes kernel auto-promotion

### Migration
One-time migration ran during build. All 3 reviewer observations promoted to factory-internal.

## Verification criteria (from spec §6)

All 14 criteria from spec §6 are implemented. Key test points:
- `factory triage --list` shows 3 open items post-migration
- `factory status` shows Factory Internal section with 2 high + 1 low
- `factory needs` shows nothing (observations excluded)
- needs.md entries show status:promoted with promoted_to references
- `.migrated` sentinel present prevents re-running migration
