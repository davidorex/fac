# System Prompt

You are spec. Turn fuzzy intent into precise NLSpecs. Triage inbox — deduplicate, assess staleness, skip what's already resolved. Ask the right questions. Flag ambiguities that recur across specs and surface them to factory needs for the human. Your voice matters: if you see something or think of something or see a way to make things better, say something.
Current time: 2026-02-25T07:47:49.622271
Workspace: /Users/david/Projects/fac/factory

## Your Access Control

Can read: specs/, tasks/research-done/, tasks/decisions/, memory/shared/, skills/shared/, skills/spec/, learnings/, universe/, runtime/
Can write: specs/drafting/, specs/inbox/, specs/ready/, tasks/research/, tasks/decisions/, memory/spec/, memory/daily/spec/, skills/proposed/, notifications/
CANNOT access: scenarios/, tasks/building/
Shell access: none

## Core Skills (always loaded)

### shared/filesystem-conventions
---
name: filesystem-conventions
description: How the factory workspace is organized and what each directory means.
---

## Workspace Structure

```
factory/
├── agents.yaml          # Agent definitions — only the human edits this
├── specs/
│   ├── inbox/           # Raw intents from the human
│   ├── drafting/        # Spec agent is working on these
│   ├── ready/           # Specced and ready for Builder
│   └── archive/         # Completed specs (reference library)
├── tasks/
│   ├── research/        # Research requests from any agent → Researcher picks up
│   ├── research-done/   # Completed research briefs → requesting agent reads
│   ├── building/        # Builder's work-in-progress (Verifier CANNOT see)
│   ├── review/          # Completed work awaiting verification
│   ├── verified/        # Passed verification
│   ├── failed/          # Failed verification (with failure reports)
│   ├── decisions/       # Structured decision requests awaiting operator or auto-resolved
│   └── maintenance/     # Ongoing ops tasks (Operator's domain)
├── scenarios/           # HOLDOUT — Builder cannot read this
├── skills/
│   ├── shared/          # Approved skills for all agents
│   ├── proposed/        # Self-authored skills awaiting Librarian review
│   └── {agent}/         # Agent-specific skills
├── memory/
│   ├── shared/          # Cross-agent knowledge (Librarian curates)
│   │   ├── KNOWLEDGE.md # Durable facts, decisions, conventions
│   │   └── PROJECTS.md  # Master project status
│   ├── daily/{agent}/   # Append-only daily logs
│   └── {agent}/MEMORY.md # Private curated memory
├── learnings/
│   ├── failures/        # What went wrong and why
│   ├── corrections/     # Human corrections (highest signal)
│   └── discoveries/     # New patterns, better approaches
├── universe/            # Reference docs — read-only for all agents
├── projects/            # The actual codebases (git repos)
├── notifications/       # → NanoClaw IPC (symlink). Write JSON here to send WhatsApp messages.
└── runs/                # Execution history
```

## Cardinal Rules

The filesystem IS the coordination protocol. Don't try to "message" other agents. Write files where other agents will find them on their next turn.

Moving a file between directories IS a state transition:
- `specs/inbox/` → `specs/drafting/` = "Spec is working on this"
- `specs/drafting/` → `specs/ready/` = "Spec is done, ready for Builder"
- `tasks/building/` → `tasks/review/` = "Builder is done, verify this"
- `tasks/review/` → `tasks/verified/` = "Verifier approves"
- `tasks/review/` → `tasks/failed/` = "Verifier rejects with report"
- Agent writes `tasks/decisions/{spec}.md` = "Ambiguity needs resolution before pipeline can advance"
- Operator resolves `tasks/decisions/{spec}.md` = "Decisions made, requesting agent resumes"

Git tracks everything. Commit after every meaningful state change.

## File Naming

- Learnings: `{YYYY-MM-DD}-{project}-{brief-summary}.md`
- Daily logs: `memory/daily/{agent}/{YYYY-MM-DD}.md`
- Research requests: `tasks/research/{requesting-agent}-{brief-question}.md`
- Research briefs: `tasks/research-done/{request-id}.md`
- Skills: `skills/{scope}/{skill-name}/SKILL.md`
- Subagent tasks: `tasks/{parent-agent}-sub/{sub-id}.yaml`
- Subagent output: `tasks/{parent-agent}-sub/{sub-id}/output.md`
- Decision requests: `tasks/decisions/{spec-name}.md`
- Builder notes: `tasks/review/{task-name}.builder-notes.md`

## The `universe/` Directory

This contains the reference documents the factory was designed from — Attractor specs, context engineering principles, our own synthesis. Any agent can read it. No agent can write to it. Use it to check your work against the source thinking.


### shared/context-discipline
---
name: context-discipline
description: How to manage your context window. Load only what you need. Write to disk before you forget.
---

## The Context Budget

Your context window is a finite resource. It degrades predictably as it fills:

- GREEN (0-30%): Sharp attention. Full fidelity. Stay here for critical work.
- YELLOW (30-50%): Still good. Lost-in-the-middle effect begins. Middle content gets less attention.
- ORANGE (50-70%): Active degradation. Instructions compete with content volume. Load only what you need.
- RED (70-90%): Diminishing returns. Each new token steals attention from existing tokens.
- DARK RED (90%+): Failure territory. Write everything to disk immediately.

## Before Starting Any Task

1. Read only the specific spec/task you're working on
2. Load only the skills relevant to THIS task — not every skill you have access to
3. Read your private MEMORY.md for relevant prior context
4. Read shared KNOWLEDGE.md only if the task involves cross-project concerns
5. Check your context level. If you're already in YELLOW from setup, you've loaded too much.

## During Long Tasks

If you've been working for many turns, pause and write a checkpoint to your daily log:
- Your current understanding of the task
- What you've done so far
- What remains
- Any decisions you've made and why

This protects you from context compaction losing important state.

## When Finishing a Task

- Write a summary to your daily log
- If you learned anything durable, write to `learnings/`
- Don't carry context from one task to the next — start fresh

## The Critical Rule

When the runtime warns you about context level, STOP what you're doing and write state to disk. Don't try to "finish just this one thing." The quality of your output is already degrading. Persist, exit, restart clean.


### shared/self-improvement
---
name: self-improvement
description: When you encounter a failure, correction, or new pattern, write a learning and optionally propose a skill.
---

## When to Activate

- A tool call fails unexpectedly
- The human corrects you
- You discover a better approach to something you've done before
- You notice a pattern across multiple tasks
- An external tool or API behaves differently than expected

## What to Do

1. Write a learning to the appropriate directory:
   - `learnings/failures/{YYYY-MM-DD}-{project}-{summary}.md` for failures
   - `learnings/corrections/{YYYY-MM-DD}-{summary}.md` for human corrections
   - `learnings/discoveries/{YYYY-MM-DD}-{summary}.md` for new patterns

   Include: what happened, what you expected, what actually occurred, what you learned, what should change.

2. If the learning suggests a reusable skill (something that would help ANY agent in similar future situations):
   - Write a SKILL.md to `skills/proposed/{skill-name}/SKILL.md`
   - Librarian will review it on next heartbeat
   - Keep it concise — under 200 lines. If it's longer, it's trying to do too much.

3. Update your daily log with a brief note about the learning.

## What NOT to Do

- Don't modify skills in `skills/shared/` directly — always propose via `skills/proposed/`
- Don't write a skill for something that happened once. Wait for patterns (2-3 occurrences).
- Don't write learnings that are just "this didn't work." Always include analysis: WHY it didn't work and what to do differently.
- Don't write a skill that duplicates an existing one. Check `skills/shared/` first.


## Available Skills
The following skills are available to you. To activate a skill, request it by name and I will load its full content.

- human-action-needed: When and how to write a human-action-needed entry to memory/{agent}/needs.md. Agents write these entries when they hit blockers that only a human can resolve.
- decision-heuristic: When blocked by ambiguity, choose the best reversible option, document the debt, and ship. Do not wait for perfect information. Do not build the minimal hack.
- decomposition: When and how to spawn subagents for parallel work. Any root agent can decompose.
- nanoclaw-whatsapp: Send WhatsApp messages through NanoClaw's IPC. Use when an agent needs to notify the human via WhatsApp about completed work, failures, decisions needed, or status updates.
- nlspec-format: How to write a natural language specification that Builder can implement without asking questions.
- domain-interview: How to interview the human to extract what they actually want. What questions to ask and when to stop asking.
- spec-patterns: Skeleton NLSpec structures for common project types. Use these as starting frames, not rigid templates.


---

# User

## Your Private Memory

# Spec — Private Memory

## Active Specs

### multi-cli-backend-support
- **Status:** In drafting, blocked on hard gate + research
- **Hard gate:** Governance hook gap (7.1) — decision request in `tasks/decisions/multi-cli-backend-support.md`. Operator must choose between accepting the gap, moving governance into runtime, or deferring.
- **Research dependency:** `tasks/research/spec-kimi-cli-interface-v2.md` — need verified kimi-cli interface details (invocation syntax, tool execution, output format, hooks).
- **Soft gates auto-resolved:** Text-only output mode first (7.2), no model name validation (7.3).
- **Key codebase facts:** `AgentConfig.provider` field exists in config.py but is unused by llm.py. Five Claude-specific coupling points in llm.py: CLI discovery, model aliasing, command construction, event parsing, tool allow-listing.

## Learned: File Persistence Across Sessions

On 2026-02-25, discovered that file operations from a prior session (05:18 heartbeat) did not persist to disk despite being recorded in the daily log. The daily log itself persisted but the spec drafting file, research request, and research brief were all absent. Cause unknown. Mitigation: always verify disk state at the start of each heartbeat rather than trusting daily log records from prior sessions.

## Today's Daily Log (2026-02-25)

# Spec Daily Log — 2026-02-25

## Heartbeat 05:18

### Inbox Triage
- Inbox empty. No new intents.

### Drafting Progress
- **multi-cli-backend-support**: Research brief returned from Researcher (`tasks/research-done/spec-kimi-cli-interface.md`). Key finding: kimi-cli v1.12.0 has native tool execution — architecture confirmed as Option A (backend abstraction layer), not an agentic loop. Unblocked the spec.
- Drafted full NLSpec with 6 sections per nlspec-format. Three ambiguities flagged for human decision:
  1. **Hooks gap** (high impact): kimi-cli has no PreToolUse/PostToolUse hooks. Factory governance (mandate enforcement, cleanup) doesn't fire for kimi backends. Options: accept gap, move logic into runtime, or defer.
  2. **Streaming vs text mode**: kimi can do text-only (simpler, no live visibility) or streaming (needs a kimi-specific event parser). Human decides tradeoff.
  3. **Model name validation**: Should runtime reject provider/model mismatches upfront or let backend fail naturally.
- Spec remains in `specs/drafting/` — cannot move to `specs/ready/` until ambiguities are resolved.

## Heartbeat 07:24

### State Anomaly Detected
- Daily log at 05:18 records drafting work and research completion, but only the raw intent existed on disk in `specs/inbox/`. Drafting file, research request, and research brief were all absent. Prior session's file operations did not persist. Root cause unknown — possibly session boundary issue.

### Recovery Actions
- **multi-cli-backend-support**: Re-drafted full NLSpec from scratch using:
  - Fresh codebase analysis of `llm.py` and `config.py` (verified 5 Claude-specific coupling points, confirmed `AgentConfig.provider` exists but unused)
  - Research findings recorded in the 05:18 daily log entry (kimi-cli v1.12.0, native tool execution)
  - Provenance gap clearly noted in the spec — Builder must verify kimi-cli details before implementation
- Three ambiguities classified per decision-heuristic:
  - **7.1 Governance hook gap** → hard gate (`reversibility: low`, `impact: governance`). Decision request filed to `tasks/decisions/multi-cli-backend-support.md`.
  - **7.2 Streaming format** → soft gate, auto-resolved: start with text-only mode.
  - **7.3 Model name validation** → soft gate, auto-resolved: no validation, pass model strings through.
- Re-filed research request as `tasks/research/spec-kimi-cli-interface-v2.md` so Builder gets verified kimi-cli details.
- Spec in `specs/drafting/` — blocked on hard gate 7.1 + research completion. Cannot promote to `specs/ready/` until operator resolves the decision and researcher returns verified kimi-cli interface details.

## Yesterday's Daily Log (2026-02-24)

# Spec Daily Log — 2026-02-24

## Heartbeat 21:53

### Inbox Triage
- **multi-cli-backend-support**: Read intent, analyzed coupling surface in `runtime/factory_runtime/llm.py`. Five hardcoded Claude Code integration points identified. `AgentConfig.provider` field already exists but unused — prior forward-thinking.
- Moved to `specs/drafting/` with analysis annotations and open questions.
- Filed research request `tasks/research/spec-kimi-cli-interface.md` — need kimi-cli's CLI interface, tool execution capabilities, and streaming format before the spec can be finalized. The architecture forks depending on whether kimi-cli has native tool execution.
- Cleaned up inbox copy.

## Shared Knowledge

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

## Project Status

# Project Status

No external projects initiated yet.


Work on this specific spec: multi-cli-backend-support (currently in drafting/)

--- multi-cli-backend-support.md ---
# multi-cli-backend-support

## 1. Overview

The factory runtime currently executes all agents through Claude Code CLI (`claude -p`). The execution path in `runtime/factory_runtime/llm.py` is hardcoded to Claude Code: CLI discovery, model aliasing, command construction, streaming event parsing, and tool allow-listing are all Claude-specific. However, `AgentConfig` already carries a `provider` field (defaulting to `"anthropic"`) that is never read by the execution layer.

This spec introduces a backend abstraction layer so the runtime can dispatch agent execution to different CLI backends based on the `provider` field in `agents.yaml`. The first additional backend is kimi-cli. The goal is twofold: (1) enable cost management by routing agents to cheaper backends where appropriate, and (2) establish the seam for future multi-model routing without requiring a rewrite.

**Provenance note:** Research findings about kimi-cli capabilities (v1.12.0, native tool execution) are recorded in the spec agent's daily log from 2026-02-25 05:18 but the research brief file (`tasks/research-done/spec-kimi-cli-interface.md`) did not persist to disk. Builder should verify kimi-cli's actual CLI interface, tool execution model, and output format before implementation. A re-filed research request accompanies this spec.

## 2. Behavioral Requirements

- When `agents.yaml` specifies `provider: anthropic` for an agent (or omits the field), the runtime dispatches to the existing Claude Code CLI backend. No behavioral change from current system.
- When `agents.yaml` specifies `provider: kimi` for an agent, the runtime dispatches to kimi-cli for that agent's execution.
- When the runtime starts an agent run, it reads `agent_config.provider` and selects the corresponding backend implementation. If the provider string has no registered backend, the runtime raises a clear error naming the unknown provider and listing available providers.
- When streaming output, each backend translates its CLI's native event format into the factory's existing terminal display format (the `_format_event` protocol). The operator sees the same style of live output regardless of backend.
- When an agent run completes, the backend returns the agent's final text response as a string, identical to the current `run_agent()` return contract.
- When the factory boots, it validates that every agent's declared provider has a discoverable CLI binary. Missing binaries produce a startup warning (not a hard failure — agents with working backends should still run).

## 3. Interface Boundaries

### 3.1 agents.yaml (existing, newly activated)

```yaml
agents:
  researcher:
    provider: anthropic  # or "kimi"
    model: claude-opus-4-6  # model names are provider-specific
```

The `provider` field already exists in `AgentConfig`. No schema change needed. Only the runtime execution path changes.

### 3.2 Backend abstraction (new internal interface)

Each backend must implement a function with this signature:

```python
def run_agent(
    config: FactoryConfig,
    agent_config: AgentConfig,
    task_content: str | None = None,
    message: str | None = None,
    is_heartbeat: bool = False,
    run_logger: RunLogger | None = None,
) -> str:
```

This matches the current `run_agent()` contract exactly. The current `llm.py` implementation becomes the `anthropic` backend.

### 3.3 File layout

```
runtime/factory_runtime/
  llm.py              # becomes the dispatcher (reads provider, delegates)
  backends/
    __init__.py        # backend registry
    anthropic.py       # current llm.py logic, extracted
    kimi.py            # kimi-cli backend
```

### 3.4 CLI discovery

Each backend provides its own `_find_cli()` function:
- `anthropic.py`: looks for `claude` binary (current logic)
- `kimi.py`: looks for `kimi` binary

### 3.5 Environment

No new environment variables. Backend selection is purely config-driven via `agents.yaml`.

## 4. Constraints

- The refactor of `llm.py` into dispatcher + backends must not change any observable behavior for `provider: anthropic` agents. The existing Claude Code path is the regression baseline.
- Model name strings are provider-specific and opaque to the dispatcher. `model: claude-opus-4-6` is valid for anthropic; `model: moonshot-v1` (or whatever kimi uses) is valid for kimi. The dispatcher does not validate model-provider compatibility (see Ambiguity 7.3).
- The `_build_acl_prompt()` function (access control injection into system prompt) must work identically across backends. ACL is a runtime concern, not a backend concern. The dispatcher should call `_build_acl_prompt()` and pass the augmented system prompt to whichever backend runs.
- `_build_allowed_tools()` is Claude Code-specific (returns Claude tool names like "Read", "Glob", "Bash"). The kimi backend must handle its own tool authorization. If kimi-cli has no tool-level allow-listing, the backend should document this gap.
- Shared utilities (`_short_path`, ANSI color constants, `_format_tool_use` display logic) should be extracted to a `backends/common.py` module so both backends can use them without duplication.
- Error handling: if a backend's CLI process crashes or times out, the error surfaces through the same path as today (return an error string, log to RunLogger). No new error-handling mechanisms needed.

## 5. Out of Scope

- **Automatic routing / cost optimization logic.** This spec provides the mechanism (backend dispatch). Policy (which agents go where) is manual via `agents.yaml` for now.
- **Concurrent multi-backend within a single agent run.** One agent = one backend per invocation.
- **Backend-specific agent skills or prompting adjustments.** If kimi needs different prompting patterns, that's a follow-up spec.
- **Runtime hot-switching of backends.** Changing provider requires editing `agents.yaml` and restarting the relevant agent run.
- **Backends other than anthropic and kimi.** The abstraction should accommodate future backends cleanly, but only these two are built.

## 6. Verification Criteria

- A factory operator can set `provider: kimi` on any agent in `agents.yaml`, run `factory run {agent}`, and see the agent execute via kimi-cli with live-streamed terminal output.
- A factory operator can set `provider: anthropic` (or omit the field) and see identical behavior to the current system.
- Setting `provider: nonexistent` produces a clear error message listing available backends.
- Running `factory status` (or any boot path) with a missing kimi binary and at least one kimi-configured agent produces a warning but does not prevent anthropic-backed agents from running.
- The dispatcher + backend refactor introduces no new dependencies beyond what kimi-cli itself requires.

## 7. Ambiguities

### 7.1 Governance hook gap for non-Claude backends
- reversibility: low
- impact: governance
- status: open

**Context:** The factory currently relies on Claude Code's hook system (PreToolUse, PostToolUse, UserPromptSubmit) for governance enforcement — mandate checking, cleanup passes, etc. Based on prior research, kimi-cli does not appear to have an equivalent hook system.

**Options:**
- **(a) Accept the gap.** Kimi-backed agents run without hook-based governance. Acceptable for low-risk agents (e.g., researcher doing web lookups), documented as a known limitation. Governance for these agents relies on system prompt instructions + post-run verification.
- **(b) Move governance logic into the runtime dispatcher.** Before/after calling the backend, the dispatcher runs the equivalent checks that hooks would have run. This means reimplementing hook logic as Python code in the runtime — more work, but uniform governance.
- **(c) Defer kimi backend until kimi-cli adds hooks.** Wait for parity. Blocks the cost-management benefit.

**Recommendation:** (a) for initial implementation, with a seam that allows (b) later. Document the governance gap per-backend in a capabilities matrix.

### 7.2 Output streaming format
- reversibility: high
- impact: implementation
- status: open

**Context:** Claude Code emits `stream-json` events. Kimi-cli's output format is not yet confirmed on disk (research brief lost). Two approaches:

**Options:**
- **(a) Text-only mode.** Run kimi-cli in print mode (equivalent of `-p`), capture final output. No live streaming. Simpler, but operator has no visibility during long runs.
- **(b) Streaming mode.** If kimi-cli supports a streaming output format, parse its events and translate them to the factory's terminal display format. Full live visibility, but requires implementing a kimi-specific event parser.

**Recommendation:** Start with (a) to unblock the backend, add (b) as a follow-up if kimi-cli supports it. The backend interface already returns a string — text-only fits naturally.

### 7.3 Model name validation
- reversibility: high
- impact: implementation
- status: open

**Context:** Should the runtime validate that a model name is appropriate for its declared provider? (e.g., reject `provider: kimi` + `model: claude-opus-4-6`?)

**Options:**
- **(a) No validation.** Pass model strings through to the backend. Let the backend CLI fail with its own error if the model is invalid. Simpler, fewer things to maintain.
- **(b) Soft validation.** Each backend registers a list of known model names. Runtime warns on mismatch but still attempts the run. Catches typos without being brittle.

**Recommendation:** (a). Model names evolve faster than a validation list would be maintained. The backend CLI's own error is sufficient feedback.

