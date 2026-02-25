# Reviewer — Human Action Needed

## NEED-R001: Universe reference doc has 5 inaccuracies
- category: observation
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T0925-high-universe-reference-tool-capabilities-md-has-5-empi.md
- filed: 2026-02-25T08:17
- source: tasks/research-done/spec-kimi-cli-interface-v2.md

`universe/reference/tool-capabilities.md` has 5 empirically verified inaccuracies about kimi-cli (detailed in research brief). Universe/ is read-only — only the operator can correct these. Per values.md: "Your tools evolve. So do you" — stale reference docs undermine tool awareness.

## NEED-R002: GC gap — tasks/decisions/ has no cleanup pass
- category: observation
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T0925-high-the-three-kernel-gc-passes-cleanup-specs-cleanup-t.md
- filed: 2026-02-25T08:17

The three kernel GC passes (cleanup-specs, cleanup-tasks, cleanup-research) do not cover `tasks/decisions/`. Resolved decisions with verified tasks accumulate. `tasks/decisions/multi-cli-backend-support.md` is the first instance — all entries resolved, task verified, file still present. A `cleanup-decisions` pass would remove decision files when the corresponding spec is archived and the task is verified.

## NEED-R003: 4 agents never write daily logs
- category: observation
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T0925-low-builder-verifier-librarian-and-operator-have-empty.md
- filed: 2026-02-25T08:17

Builder, verifier, librarian, and operator have empty daily log directories. Builder and verifier both ran on 2026-02-25 but wrote no logs. The context-discipline skill mandates daily log writes on task completion. Either the skill instruction is not reaching these agents effectively or they are deprioritizing it. This degrades traceability (values.md: "Every artifact should be traceable").

## reviewer-review-protocol-in-available-not-always
- status: resolved
- resolved_at: 2026-02-26T05:49:22
- resolved_by: kernel-sudo
- created: 2026-02-25T21:04:00Z
- category: config-edit
- blocked: The `reviewer/review-protocol` skill defines my entire review process — Steps 1-5, evidence requirements, the 3-intent limit, deduplication checks. It is in `available`, not `always`. Every productive run requires it. My heartbeat and this reflection both depend on it. Without it loaded, I operate from internalized structure that may drift from the canonical protocol. This is the same pattern surfaced by spec (nlspec-format), builder (implementation-approach, convergence), librarian (knowledge-curation, pattern-detection, memory-hygiene), and operator (monitoring skills) — core operational skills listed as `available` rather than `always`.
- context: Reflection pass 2026-02-25. Reviewed agents.yaml skills block for reviewer. Cross-referenced with other agents' reflection observations — 4 of 7 agents identified the same pattern independently.

### Exact Change
In agents.yaml, move `reviewer/review-protocol` from `available:` to `always:` under the reviewer agent's skills block.

## reviewer-empty-private-memory
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T2108-high-private-memory-md-is-empty-no-entries-yet-after-1.md
- created: 2026-02-25T21:04:00Z
- category: observation
- blocked: Private MEMORY.md is empty ("No entries yet") after 1 heartbeat run that produced 4 findings and 3 needs entries, plus this reflection pass. Knowledge accumulated across runs — pipeline conventions, factory-internal observation patterns, access scope questions, the available-vs-always skill pattern across agents — exists only in daily logs and this needs.md file. Each new reviewer session starts cold. Same systemic issue surfaced by all 7 agents during reflection.
- context: Reflection pass 2026-02-25. Read memory/reviewer/MEMORY.md, found only placeholder text. Cross-referenced with other agents' needs.md — all 7 report the same gap.

### Exact Change
The root cause is systemic: the `shared/self-improvement` skill covers `learnings/` and `skills/proposed/` but says nothing about when to curate private MEMORY.md. Every agent has this gap. Two paths: (1) Add MEMORY.md curation guidance to `shared/self-improvement` — "after each productive run, persist durable knowledge to MEMORY.md." (2) Add a post-run kernel prompt that reminds the agent to curate. Option 1 is lighter and within existing architecture. Immediate self-correction: reviewer will populate MEMORY.md at end of this reflection.

## reviewer-access-scope-missing-pipeline-directories
- status: open
- created: 2026-02-25T21:04:00Z
- category: config-edit
- blocked: My `can_read` scope does not include `tasks/decisions/` or `tasks/research-done/`. My 08:17 heartbeat review checked both directories and reported findings (stale decision file, consumed research brief). This means either the runtime did not enforce the access restriction, or my review operated outside its declared scope. Both are problems. My review-protocol implicitly requires pipeline health assessment, which means reading pipeline state across all `tasks/` subdirectories, not just `verified/` and `failed/`. The spec agent's `can_read` includes `tasks/research-done/` and `tasks/decisions/`; my scope should at minimum match what I need to review pipeline staleness.
- context: Reflection pass 2026-02-25. Compared `can_read` from agents.yaml against directories actually accessed during 08:17 heartbeat. Found 2 directories accessed that are not in declared scope.

### Exact Change
In agents.yaml, add `tasks/decisions/` and `tasks/research-done/` to the reviewer's `can_read` list. These directories contain artifacts whose lifecycle I need to assess (staleness, orphaned files, GC gaps). Alternatively, if the intent is to keep reviewer scope narrow, update the review-protocol to explicitly exclude pipeline staleness checks for these directories.

## reviewer-no-factory-internal-synthesis-in-protocol
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T2108-high-my-review-protocol-step-1-performs-deduplication-a.md
- created: 2026-02-25T21:04:00Z
- category: observation
- blocked: My review-protocol (Step 1) performs deduplication against `specs/inbox/`, `specs/drafting/`, `specs/ready/`, `specs/archive/`. It does not include `specs/factory-internal/` in the deduplication scan, nor does it have a step for synthesizing thematically related factory-internal observations into consolidated improvement intents. After this evening's reflection passes, `specs/factory-internal/` contains 28 observations. Many are thematic duplicates: empty MEMORY.md appears 6 times (one per agent), missing daily logs appears 4+ times, available-vs-always skills appears 4+ times. My role is to "close the loop" — identify patterns and generate deduplicated intents. The protocol lacks the step that processes factory-internal observations into consolidated actions.
- context: Reflection pass 2026-02-25. Counted 28 factory-internal observations after reflection passes. Identified at least 3 themes each repeated 4-6 times across agents. My review-protocol has no Step for this synthesis.

### Exact Change
Add a step to `reviewer/review-protocol` between current Step 1.5 (Needs Escalation Check) and Step 2 (Review Categories): "Step 1.75: Factory Internal Synthesis — Read `specs/factory-internal/`. Cluster observations by theme. For themes with 3+ observations across agents, generate a single consolidated intent in `specs/inbox/` that addresses the systemic pattern rather than individual instances. Note: this replaces individual observations, not supplements them."
