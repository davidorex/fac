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
`factory cleanup-specs`, `factory cleanup-tasks`, and `factory cleanup-research` run as post-execution hooks after every agent run:
- **Spec cleanup**: removes upstream spec copies (inbox/, drafting/) when a downstream stage already holds the same filename
- **Task cleanup**: removes stale `tasks/review/` files when an exact-name match exists in `tasks/verified/` or `tasks/failed/`
- **Research cleanup**: removes stale `tasks/research/` requests when an exact-name match exists in `tasks/research-done/`

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
Agents write to `memory/{agent}/needs.md` when hitting blockers that require human intervention (READ-ONLY file edits, access scope changes, external actions). `factory needs` surfaces all open entries grouped by category. `factory needs --resolve {id}` marks entries resolved. `observation` category entries (non-blocking, from reflection passes) display separately and can be hidden with `--blockers-only`.

### Scenario Holdouts
`scenarios/` is inaccessible to Builder — holdout by design. Project scenarios live in `scenarios/{project}/`. The meta-scenario for factory infrastructure is `scenarios/meta/factory-itself.md`. Verifier evaluates against holdout scenarios independently; meta-scenario evaluation is directional (not pass/fail). Commands: `factory scenario init-meta`, `factory scenario new`, `factory scenario list`.

### Agent Reflection
`factory reflect [AGENT]` runs sequential reflection passes across pipeline agents (or a single named agent). Each agent receives its own agents.yaml config block plus the `agent-reflection` skill content, and writes observations to its `memory/{agent}/needs.md`. Observations have `category: observation` and appear separately in `factory needs` output.

### Decision Gates
When agents hit ambiguities during spec or build, the decision-heuristic skill classifies them:
- **Soft gate** (`reversibility: high` + `impact: implementation|cosmetic`): agent auto-resolves, builds a seam, documents in builder-notes. Work continues.
- **Hard gate** (`reversibility: low` OR `impact: governance`): agent writes structured decision request to `tasks/decisions/{spec}.md`. Pipeline blocks. Operator resolves via `factory decide {spec} --entry {id} --answer {choice}`.

The structured ambiguity format (in specs §7) uses tagged entries with `reversibility:` and `impact:` fields so the pipeline can route correctly.

### Pipeline Next-Step Display
After each agent run, the runtime prints downstream directories with pending counts and actionable commands — guides the human on what to run next. When `tasks/decisions/` has items, the hint is `factory decide` (not `factory run researcher`).

## Known System Quirks

### `rm` Interactive Alias
`rm` is aliased to interactive mode on this system. Do not use `rm` in scripts or automated contexts. Use `python3 -c "import os; os.remove('path')"` for filesystem deletions, or `git rm` for tracked files that should be removed from the index.

### Git Staging for Deleted Files
When a file is deleted from disk but was previously staged (creating `AD` status), use `git rm path/to/file` followed by a new commit — not `--amend`. Amending risks destroying previous commit content.
