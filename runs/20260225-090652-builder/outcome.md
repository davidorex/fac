# Outcome

Done. Task is in `tasks/review/`. Here's what was built:

---

**`no-ephemeral-suggestions` implemented.** `tasks/review/` — awaiting verifier.

## What shipped

**`specs/factory-internal/`** — new directory. All observation files land here, dated and severity-tagged (`{YYYY-MM-DDTHHMM}-{severity}-{slug}.md`).

**`factory triage`** — new command. `--list` shows open observations by severity/age. `--promote` writes raw intent to `specs/inbox/`. `--dismiss --reason "..."` closes without pipeline entry. No-arg display shows full observation + available actions. Slug partial-match supported; multi-match exits with error.

**`factory cleanup-factory-internal`** — standalone GC pass. Removes promoted files whose `promoted_to` spec is archived; dismissed files older than 30 days.

**`factory status`** — new "Factory Internal" section showing open counts grouped by severity (critical→high→low).

**`factory needs`** — observations excluded entirely. `--blockers-only` retained as a no-op.

**`factory run` / `advance` / `reflect`** — new post-execution passes: safety-net extraction → promote_needs_observations → cleanup_factory_internal → migration.

**Skills updated** — `human-action-needed` and `self-improvement` note kernel auto-promotion and direct agents to `factory triage --list`.

**Migration ran** — all 3 reviewer observations (NEED-R001/R002/R003) promoted to `specs/factory-internal/` during build. `memory/reviewer/needs.md` entries marked `status: promoted`. `.migrated` sentinel written.
