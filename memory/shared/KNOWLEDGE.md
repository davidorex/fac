# Shared Knowledge

## Factory Philosophy

This factory was designed from the convergence of four projects: OpenClaw (self-improving agent skills), Agent Skills for Context Engineering (progressive disclosure and attention budgeting), StrongDM's Attractor (graph-based pipeline orchestration with NLSpecs), and Simon Willison's Software Factory analysis (scenario holdouts and satisfaction metrics).

Core principles:
- The filesystem is the coordination substrate. No messages, no queues. Write files where other agents will find them.
- Specifications are the unit of work. Humans write intent. Agents write implementations.
- Trust comes from the environment, not from individual agent intelligence. Verification is structural.
- Context is the bottleneck. Load only what you need. Write to disk before you forget.
- Self-improvement is collective. Failures become learnings become skills become shared capability.

## Active Conventions

- Commit after every meaningful state change
- Move files between directories to signal state transitions
- Always check universe/ before going external for research
- Proposed skills go to skills/proposed/ — only Librarian promotes to skills/shared/

## Established Pipeline Conventions

### Spec Lifecycle
Specs are archived by Builder *before* implementation begins — Builder moves the spec from `specs/ready/` to `specs/archive/` as the first act of picking up work. This prevents double-processing and maintains clean state.

### Pipeline Cleanup (Automatic)
Four GC passes run as post-execution hooks after every agent run (`factory run`, `factory advance`, `factory reflect`):
- **Spec cleanup** (`cleanup-specs`): removes upstream spec copies (inbox/, drafting/) when a downstream stage already holds the same filename
- **Task cleanup** (`cleanup-tasks`): removes stale `tasks/review/` files when an exact-name match exists in `tasks/verified/` or `tasks/failed/`
- **Research cleanup** (`cleanup-research`): removes stale `tasks/research/` requests when an exact-name match exists in `tasks/research-done/`
- **Factory internal cleanup** (`cleanup-factory-internal`): removes promoted factory-internal files whose `promoted_to` spec is archived; removes dismissed files older than 30 days. Standalone: `factory cleanup-factory-internal [--dry-run]`

### Failure Learning Convention
Every failure report in `tasks/failed/` MUST include a `## Generalizable Learning` section. The runtime automatically extracts these to `learnings/failures/` after each Verifier run. Absence of this section is logged as a warning but does not block the pipeline.

### Rebuild Protocol
Failed tasks can be rebuilt via `factory rebuild {task-name}`. The command:
1. Copies the archived spec to `specs/ready/` with a rebuild brief
2. Versions the failure report to `tasks/failed/{name}.v{N}.md`
3. Commits the state transition

### Failed Task Lifecycle
`tasks/resolved/` holds failure reports that have been addressed (by rebuild or manual resolution). After a rebuilt task is verified, the old failure report moves to `tasks/resolved/` with a `## Resolution` annotation. `factory resolve {task-name} --reason "..."` handles manual resolution.

### Human-Action-Needed System
Agents write to `memory/{agent}/needs.md` when hitting blockers that require human intervention (READ-ONLY file edits, access scope changes, external actions). `factory needs` surfaces all open **blocker** entries grouped by category. `factory needs --resolve {id}` marks entries resolved. `--blockers-only` is a backward-compatible no-op (observations no longer appear in `factory needs` at all).

`category: observation` entries are **automatically promoted** by the kernel post-run pass (`promote_needs_observations()`) to `specs/factory-internal/` with `status: promoted`. The kernel also extracts signal phrases from agent prose output (`extract_surfaced_observations()`) into factory-internal. Operators manage observations via `factory triage` (not `factory needs`).

### Scenario Holdouts
`scenarios/` is inaccessible to Builder — holdout by design. Project scenarios live in `scenarios/{project}/`. The meta-scenario for factory infrastructure is `scenarios/meta/factory-itself.md`. Verifier evaluates against holdout scenarios independently; meta-scenario evaluation is directional (not pass/fail). Commands: `factory scenario init-meta`, `factory scenario new`, `factory scenario list`.

### Agent Reflection
`factory reflect [AGENT]` runs sequential reflection passes across pipeline agents (or a single named agent). Each agent receives its own agents.yaml config block plus the `agent-reflection` skill content, and writes observations to its `memory/{agent}/needs.md`. Observations have `category: observation` and are automatically promoted to `specs/factory-internal/` by the kernel post-run pass — they do not appear in `factory needs` output.

### Multi-Backend Dispatch Architecture
`llm.py` is a dispatcher; backends live in `runtime/factory_runtime/backends/`. `get_backend(provider)` in `backends/__init__.py` returns the correct backend. `validate_providers()` checks binary availability at startup — missing binary produces a warning but does not block other agents.

Current backends:
- `backends/anthropic.py` — Claude Code CLI, full stream-json event parsing, identical to pre-refactor behavior
- `backends/kimi.py` — kimi-cli backend, temp file cleanup in `finally` block, no streaming

**Backend `run_agent()` signature:** `(config, agent_config, task_content, message, is_heartbeat, run_logger, system_prompt, user_prompt) → str`

**Invariants:** Context assembly (`assemble_context()`) and ACL injection (`_build_acl_prompt()`) happen in the dispatcher, not in backends. Governance (`run_pre_governance()`, `run_post_governance()`) is backend-agnostic. `provider:` field in `agents.yaml` determines which backend runs an agent. `backends/capabilities.md` documents the capability matrix including accepted gaps (per-tool-call governance for kimi, no streaming).

### Factory Internal Observation Pipeline
`specs/factory-internal/` holds structured observations promoted from agent needs.md or extracted from prose. Lifecycle: `open` → `promoted` (becomes inbox spec via `factory triage {slug} --promote`) or `dismissed` (`factory triage {slug} --dismiss --reason "..."`).

**File naming:** `{YYYY-MM-DDTHHMM}-{severity}-{slug}.md`. Severity: `critical`, `high`, `low` (keyword heuristics via `_CRITICAL_TERMS` / `_HIGH_TERMS`).

**Kernel auto-promotion:** After every agent run, `promote_needs_observations()` converts `category: observation, status: open` needs.md entries to factory-internal files (`source-type: needs-promotion`). Needs entries updated to `status: promoted` with `promoted_to` field. Separately, `extract_surfaced_observations()` scans agent prose for signal phrases and creates factory-internal entries (`source-type: kernel-extraction`), capped at 3 per run with deduplication.

**Operator commands:**
- `factory triage --list` — severity-grouped view (critical → high → low), oldest first. `--all` includes promoted/dismissed.
- `factory triage {slug} --promote` — creates `specs/inbox/{slug}.md` with observation text
- `factory triage {slug} --dismiss --reason "..."` — requires reason; exit 1 if omitted
- Slug resolution accepts full filename or substring; ambiguous → lists matches + exit 1

**`factory status`** shows Factory Internal section with severity-grouped counts and slug names when open observations exist; section omitted entirely when empty. Critical items generate `factory triage {file} --promote` hints in next-step display (capped at 2).

### Decision Gates
When agents hit ambiguities during spec or build, the decision-heuristic skill classifies them:
- **Soft gate** (`reversibility: high` + `impact: implementation|cosmetic`): agent auto-resolves, builds a seam, documents in builder-notes. Work continues.
- **Hard gate** (`reversibility: low` OR `impact: governance`): agent writes structured decision request to `tasks/decisions/{spec}.md`. Pipeline blocks. Operator resolves via `factory decide {spec} --entry {id} --answer {choice}`.

The structured ambiguity format (in specs §7) uses tagged entries with `reversibility:` and `impact:` fields so the pipeline can route correctly.

### Pipeline Next-Step Display
After each agent run, the runtime prints downstream directories with pending counts and actionable commands — guides the human on what to run next. Hints include spec/task names when there's a single item (copy-pasteable commands). When specs are in `drafting/` with research or decisions available, the hint says `factory advance NAME` instead of `factory run spec`. When `tasks/decisions/` has unresolved hard gates, the hint is `factory decide`.

### factory advance Command
`factory advance SPEC` is semantically distinct from `factory run spec SPEC`. It gathers all unblocking context (research briefs from `tasks/research-done/`, resolved decisions from `tasks/decisions/`, and the current spec content) into a single directed message for the right agent. Drafting specs go to the spec agent for finalization; ready specs go to the builder.

### WhatsApp Notifications
The kernel sends a WhatsApp message via NanoClaw IPC after every agent run (skipping NO_REPLY idle heartbeats). The notification includes a truncated agent response summary and computed next actions. All 7 agents have `shared/nanoclaw-whatsapp` skill and `notifications/` write access.

### Project Registration
`factory init-project` writes a `.factory` marker file in the current directory, pointing to the factory workspace. The CLI resolves upward from cwd to find this marker (like `.git`), so all factory commands work from within project directories. `FactoryConfig` carries `project_dir` and `project_name` when in project context.

## Known System Quirks

### `rm` Interactive Alias
`rm` is aliased to interactive mode on this system. Do not use `rm` in scripts or automated contexts. Use `python3 -c "import os; os.remove('path')"` for filesystem deletions, or `git rm` for tracked files that should be removed from the index.

### Git Staging for Deleted Files
When a file is deleted from disk but was previously staged (creating `AD` status), use `git rm path/to/file` followed by a new commit — not `--amend`. Amending risks destroying previous commit content.
