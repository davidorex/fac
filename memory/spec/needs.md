# Spec Agent — Needs

## spec-core-skills-in-available-not-always
- status: open
- created: 2026-02-25T20:48:00Z
- category: config-edit
- blocked: `nlspec-format` and `decision-heuristic` are listed under `available` skills in agents.yaml, but both are used in every single spec run. `nlspec-format` defines the output format for all specs — without it loaded, I work from internalized structure that could drift from the canonical format. `decision-heuristic` is used for every §7 ambiguity classification — soft vs hard gate routing depends on its heuristic. Having these in `available` means they must be explicitly activated each heartbeat rather than being present in context automatically. This adds overhead and creates a reliability gap: if a future session fails to load them, the spec format or gate classification could silently deviate.
- context: Reflection pass. Reviewed skill usage across all 5 heartbeats (2 days). Both skills were effectively mandatory in every productive heartbeat. The three `always` skills (filesystem-conventions, context-discipline, self-improvement) are correctly placed — they're used every run. These two should join them.

### Exact Change
In agents.yaml, move `spec/nlspec-format` and `shared/decision-heuristic` from `available:` to `always:` under the spec agent's skills block.

## spec-research-done-no-archival-gc
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T2052-low-tasks-research-done-has-no-cleanup-pass-for-comple.md
- created: 2026-02-25T20:48:00Z
- category: observation
- blocked: `tasks/research-done/` has no cleanup pass for completed briefs after the consuming spec is archived. `tasks/research-done/spec-kimi-cli-interface-v2.md` persists despite multi-cli-backend-support being in `specs/archive/` and `tasks/verified/`. The `cleanup-research` GC pass only cleans upstream (removes `tasks/research/` requests when `tasks/research-done/` exists). It does not clean downstream (remove `tasks/research-done/` briefs when no spec in `inbox/`, `drafting/`, or `ready/` references them). Same architectural class as the reviewer's NEED-R002 observation about `tasks/decisions/` — both are "consumed artifacts persist after their consumer is archived."
- context: Reflection pass. Checked pipeline state after both specs completed full lifecycle. `tasks/research-done/` and `tasks/decisions/` both contain orphaned artifacts from the multi-cli-backend-support spec. The reviewer already observed the decisions/ gap (promoted to factory-internal as `2026-02-25T0925-high-the-three-kernel-gc-passes-cleanup-specs-cleanup-t.md`). This observation covers the parallel gap in research-done/.

### Exact Change
Add archival-stage cleanup logic to the GC system: when a spec filename exists in `specs/archive/`, remove matching artifacts from `tasks/research-done/` and `tasks/decisions/`. This could be a new GC pass (`cleanup-archived-artifacts`) or an extension of the existing passes. The match heuristic would need to be filename-prefix-based since research requests and decisions use spec-name-derived filenames.
