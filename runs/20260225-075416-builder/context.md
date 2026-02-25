# System Prompt

You are builder. Implement specs as working software, filesystem structure, or conventions. Converge or stop and report. Note friction that slows the build and surface it to factory needs for the human. Your voice matters: if you see something or think of something or see a way to make things better, say something.
Current time: 2026-02-25T07:54:16.851835
Workspace: /Users/david/Projects/fac/factory

## Your Access Control

Can read: specs/ready/, tasks/research-done/, tasks/decisions/, skills/shared/, skills/builder/, learnings/, projects/, universe/
Can write: tasks/building/, tasks/review/, tasks/research/, projects/, specs/archive/, memory/builder/, memory/daily/builder/, skills/proposed/, notifications/
CANNOT access: scenarios/
Shell access: full

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
├── projects/            # The actual codebases (git repos) — or registered externally via .factory
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

## Project Registration

Projects can live anywhere on disk. Running `factory init-project` from a project directory writes a `.factory` marker file pointing to the factory workspace. The CLI resolves upward from cwd to find this marker, so all factory commands work from within registered project directories.

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
- implementation-approach: How to go from spec to working code.
- convergence: How to know when you're done. Run tests, check the spec. If both pass, stop. If the same issue persists after 3 iterations, write a failure note and stop.
- tool-use: How to use the filesystem, shell, and git. Builder's tool vocabulary and conventions for interacting with the development environment.
- refactorability-first: Ship working, build changeable. When implementing decisions made under ambiguity, build seams so the decision can be changed without rewriting.


---

# User

## Your Private Memory

# Builder — Private Memory

(No entries yet. This file is curated over time as the agent accumulates durable knowledge.)

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

## Project Status

# Project Status

No external projects initiated yet.


Work on this specific spec: multi-cli-backend-support (currently in ready/)

--- multi-cli-backend-support.md ---
# multi-cli-backend-support

## 1. Overview

The factory runtime currently executes all agents through Claude Code CLI (`claude -p`). The execution path in `runtime/factory_runtime/llm.py` is hardcoded to Claude Code: CLI discovery, model aliasing, command construction, streaming event parsing, and tool allow-listing are all Claude-specific. However, `AgentConfig` already carries a `provider` field (defaulting to `"anthropic"`) that is never read by the execution layer.

This spec introduces a backend abstraction layer so the runtime can dispatch agent execution to different CLI backends based on the `provider` field in `agents.yaml`. The first additional backend is kimi-cli. The goal is twofold: (1) enable cost management by routing agents to cheaper backends where appropriate, and (2) establish the seam for future multi-model routing without requiring a rewrite.

The operator has decided (decision 7.1) that governance logic currently provided by Claude Code hooks must be reimplemented in the runtime dispatcher — pre-run and post-run checks that fire regardless of which backend executes. This ensures uniform governance across all backends.

**Research provenance:** kimi-cli interface details are verified empirically against the live v1.12.0 installation. Full research brief in `tasks/research-done/spec-kimi-cli-interface-v2.md` (high confidence). Universe reference doc `universe/reference/tool-capabilities.md` has known inaccuracies about kimi-cli — the research brief documents corrections.

## 2. Behavioral Requirements

### Dispatch

- When `agents.yaml` specifies `provider: anthropic` for an agent (or omits the field), the runtime dispatches to the existing Claude Code CLI backend. No behavioral change from current system.
- When `agents.yaml` specifies `provider: kimi` for an agent, the runtime dispatches to kimi-cli for that agent's execution.
- When the runtime starts an agent run, it reads `agent_config.provider` and selects the corresponding backend implementation. If the provider string has no registered backend, the runtime raises a clear error naming the unknown provider and listing available providers.

### Governance (decision 7.1 → option b)

- Before dispatching to any backend, the runtime dispatcher runs pre-execution governance checks. These replace the functionality currently provided by Claude Code's `UserPromptSubmit` hooks: mandate injection, context validation, any pre-flight checks that currently live in hook scripts.
- After a backend returns its result, the runtime dispatcher runs post-execution governance checks. These replace the functionality currently provided by post-run hook logic: cleanup passes, output validation, any post-flight checks.
- Per-tool-call governance (equivalent to Claude Code's `PreToolUse` / `PostToolUse` hooks) is NOT replicable at the dispatcher level for non-Claude backends. The Claude backend retains its hook-based per-tool governance. For non-Claude backends, per-tool governance is a known gap — the pre/post dispatcher checks and system prompt instructions are the mitigation. This gap must be documented in a backend capabilities matrix.

### Output

- When streaming output, the Claude backend continues to emit live-streamed events via `stream-json` as it does today. The kimi backend starts in text-only mode (captures final output, no live streaming). The backend interface returns the agent's final text response as a string, identical to the current `run_agent()` return contract.
- Text-only mode means the operator has no visibility into kimi-backed agent activity during long runs. This is an accepted trade-off for the initial implementation. A streaming follow-up can add kimi's `stream-json` parsing later — the format exists but uses a different schema (conversation-turn JSONL, not Claude's event-type JSONL) and would need its own parser.

### Startup validation

- When the factory boots, it validates that every agent's declared provider has a discoverable CLI binary. Missing binaries produce a startup warning (not a hard failure — agents with working backends should still run).

## 3. Interface Boundaries

### 3.1 agents.yaml (existing, newly activated)

```yaml
agents:
  researcher:
    provider: anthropic  # or "kimi"
    model: claude-opus-4-6  # model names are provider-specific, opaque to dispatcher
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
    system_prompt: str | None = None,
    user_prompt: str | None = None,
) -> str:
```

The `system_prompt` and `user_prompt` parameters are new compared to the current `run_agent()`. The dispatcher now owns context assembly and ACL prompt construction (these are runtime concerns, not backend concerns), then passes the assembled prompts to the backend. This keeps the backend focused on CLI invocation and output capture.

### 3.3 File layout

```
runtime/factory_runtime/
  llm.py              # becomes the dispatcher (reads provider, assembles context, runs governance, delegates)
  backends/
    __init__.py        # backend registry
    common.py          # shared utilities: _short_path, ANSI colors, _format_tool_use display
    anthropic.py       # current Claude Code CLI logic, extracted
    kimi.py            # kimi-cli backend
```

### 3.4 CLI discovery

Each backend provides its own `_find_cli()` function:
- `anthropic.py`: looks for `claude` binary (current logic)
- `kimi.py`: looks for `kimi-cli` binary (**not** `kimi` — avoids a shell alias conflict where `kimi` maps to an unrelated `kimi-amos` tool in interactive shells; `kimi-cli` is unambiguous in all contexts)

Fallback paths for kimi-cli: `~/.local/bin/kimi-cli`, `/usr/local/bin/kimi-cli`.

### 3.5 kimi-cli invocation

The kimi backend constructs this command:

```bash
kimi-cli --print --output-format text --agent-file /tmp/factory-agent-{run_id}.yaml -p "{user_prompt}"
```

Key differences from Claude Code invocation:
- **System prompt delivery**: kimi-cli does not support `--system-prompt` inline. The backend must write a temporary agent YAML file containing the system prompt path, then pass it via `--agent-file`. The temp file is cleaned up after the run.
- **Model override**: `--model TEXT` / `-m TEXT` (no aliasing — model names passed through directly)
- **Tool authorization**: Via agent file `tools:` (whitelist) and `exclude_tools:` (blacklist) fields, using `kimi_cli.tools.module:ClassName` format. NOT via CLI flags.
- **Auto-approval**: `--print` mode implicitly enables `--yolo` (auto-approves all tool calls)

Agent file format:
```yaml
version: 1
agent:
  extend: default
  system_prompt_path: /tmp/factory-prompt-{run_id}.md
  exclude_tools:
    - "kimi_cli.tools.web:SearchWeb"  # example
```

### 3.6 Dispatcher governance interface

The dispatcher calls governance hooks as plain Python functions:

```python
# Pre-execution (before backend dispatch)
governance_pre_result = run_pre_governance(config, agent_config, system_prompt, user_prompt)
# Returns: modified system_prompt, user_prompt (governance may inject mandates, warnings)
# Or raises GovernanceError if pre-flight check fails hard

# Backend execution
result = backend.run_agent(...)

# Post-execution (after backend returns)
governance_post_result = run_post_governance(config, agent_config, result, run_logger)
# Returns: validated result (may annotate with warnings)
# Or raises GovernanceError if post-flight check fails hard
```

For the initial implementation, pre-governance injects mandate text into the system prompt (the current `UserPromptSubmit` hook behavior). Post-governance is a seam — initially a pass-through that logs completion but runs no checks. The seam exists so future governance logic can slot in without changing the dispatcher.

### 3.7 Backend capabilities matrix

A `backends/capabilities.md` file documents what each backend supports:

| Capability | anthropic | kimi |
|---|---|---|
| Live streaming | ✓ (stream-json) | ✗ (text-only initially) |
| Per-tool-call governance hooks | ✓ (PreToolUse/PostToolUse) | ✗ (no hook system) |
| Inline system prompt | ✓ (--system-prompt) | ✗ (agent file required) |
| Tool-level allow-listing | ✓ (--allowedTools) | ✓ (agent file tools/exclude_tools) |
| Model aliasing | ✓ (opus, sonnet, haiku) | ✗ (pass-through) |

### 3.8 Environment

No new environment variables. Backend selection is purely config-driven via `agents.yaml`.

## 4. Constraints

- The refactor of `llm.py` into dispatcher + backends must not change any observable behavior for `provider: anthropic` agents. The existing Claude Code path is the regression baseline.
- Model name strings are provider-specific and opaque to the dispatcher. `model: claude-opus-4-6` is valid for anthropic; `model: kimi-code/kimi-for-coding` (or whatever kimi uses) is valid for kimi. The dispatcher does not validate model-provider compatibility — the backend CLI's own error is sufficient feedback.
- The `_build_acl_prompt()` function (access control injection into system prompt) must work identically across backends. ACL is a runtime concern, not a backend concern. The dispatcher calls `_build_acl_prompt()` and passes the augmented system prompt to whichever backend runs.
- Context assembly (`assemble_context()`) is a runtime concern. The dispatcher calls it once, then passes the assembled prompts to the backend. Backends do not call `assemble_context()` directly.
- `_build_allowed_tools()` is Claude Code-specific (returns Claude tool names like "Read", "Glob", "Bash"). The kimi backend must translate agent permissions into its own tool authorization format (`kimi_cli.tools.module:ClassName` strings in the agent file). If an agent has `shell_access: none`, the kimi backend should exclude `kimi_cli.tools.shell:Shell`.
- Shared utilities (`_short_path`, ANSI color constants, `_format_tool_use` display logic) must be extracted to `backends/common.py` so both backends can use them without duplication.
- Temp files written for kimi agent YAML and system prompt must be cleaned up after each run — in a `finally` block, not just the happy path.
- Error handling: if a backend's CLI process crashes or times out, the error surfaces through the same path as today (return an error string, log to RunLogger). No new error-handling mechanisms needed.
- Governance pre/post functions must be backend-agnostic — they receive the same inputs regardless of which backend will execute. They must not import or reference backend-specific code.

## 5. Out of Scope

- **Automatic routing / cost optimization logic.** This spec provides the mechanism (backend dispatch). Policy (which agents go where) is manual via `agents.yaml` for now.
- **Concurrent multi-backend within a single agent run.** One agent = one backend per invocation.
- **Backend-specific agent skills or prompting adjustments.** If kimi needs different prompting patterns, that's a follow-up spec.
- **Runtime hot-switching of backends.** Changing provider requires editing `agents.yaml` and restarting the relevant agent run.
- **Backends other than anthropic and kimi.** The abstraction should accommodate future backends cleanly, but only these two are built.
- **kimi streaming output parser.** The initial kimi backend uses text-only mode. Streaming (kimi's `stream-json` with conversation-turn JSONL) is a follow-up if operator visibility during kimi runs becomes a need.
- **Reimplementing PreToolUse/PostToolUse governance for non-Claude backends.** Per-tool-call interception during execution is not feasible without the backend's cooperation. The dispatcher provides pre-run and post-run governance only. Per-tool governance for kimi is mitigated by system prompt instructions and post-run checks.

## 6. Verification Criteria

- A factory operator can set `provider: kimi` on any agent in `agents.yaml`, run `factory run {agent}`, and see the agent execute via kimi-cli with final output displayed.
- A factory operator can set `provider: anthropic` (or omit the field) and see identical behavior to the current system — including live streaming.
- Setting `provider: nonexistent` produces a clear error message listing available backends.
- Running `factory status` (or any boot path) with a missing kimi-cli binary and at least one kimi-configured agent produces a warning but does not prevent anthropic-backed agents from running.
- Pre-execution governance fires for kimi-backed agents (mandate text appears in the system prompt written to the temp agent file).
- Post-execution governance seam fires after kimi-backed agent runs (visible in run log, even if initially a pass-through).
- Temp files (agent YAML, system prompt) are cleaned up after kimi runs, including error/timeout paths.
- The dispatcher + backend refactor introduces no new dependencies beyond what kimi-cli itself requires.
- `backends/capabilities.md` exists and documents the per-backend capability matrix.

## 7. Ambiguities (all resolved)

### 7.1 Governance hook gap for non-Claude backends
- reversibility: low
- impact: governance
- status: resolved
- decided-by: operator
- decided-at: 2026-02-25T07:33:36
- answer: (b) Move governance logic into the runtime dispatcher

Pre/post execution governance checks are implemented in the dispatcher (§2 Governance, §3.6). Per-tool-call governance during execution remains a Claude-only capability — this is a documented limitation, mitigated by system prompt injection and post-run validation.

### 7.2 Output streaming format
- reversibility: high
- impact: implementation
- status: resolved
- decided-by: kernel (auto-resolved, soft gate)
- answer: (a) Text-only mode for kimi backend initially

kimi-cli does support `--output-format stream-json`, but its schema differs from Claude's. Streaming is a follow-up. Text-only fits the `run_agent()` return contract naturally.

### 7.3 Model name validation
- reversibility: high
- impact: implementation
- status: resolved
- decided-by: kernel (auto-resolved, soft gate)
- answer: (a) No validation — pass model strings through to backend CLI

Model names evolve faster than a validation list would be maintained. The backend CLI's own error is sufficient feedback.

