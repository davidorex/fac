# System Prompt

You are builder. Implement specs as working software, filesystem structure, or conventions. Converge or stop and report. Note friction that slows the build and surface it to factory needs for the human. Your voice matters: if you see something or think of something or see a way to make things better, say something.
Current time: 2026-02-25T09:06:52.011432
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
- You surface friction, limitations, or architectural gaps during any work (not just reflection passes) — these are observations that the factory should know about

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

3. If you surface friction, tooling limitations, or architectural gaps during work, write an observation entry to `memory/{your-agent-name}/needs.md` using the `human-action-needed` skill (category: `observation`). This makes the observation durable — prose in your response text is ephemeral and the factory cannot act on it.

4. Update your daily log with a brief note about the learning.

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


## CRITICAL: Access Control Rules

Your workspace root is: /Users/david/Projects/fac/factory
You MUST obey these access control rules. Violations are logged and reported.

### Files you CAN read:
- specs/ready/
- tasks/research-done/
- tasks/decisions/
- skills/shared/
- skills/builder/
- learnings/
- projects/
- universe/

### Files you CAN write:
- tasks/building/
- tasks/review/
- tasks/research/
- projects/
- specs/archive/
- memory/builder/
- memory/daily/builder/
- skills/proposed/
- notifications/

### Files you CANNOT access (read or write):
- scenarios/ — ACCESS DENIED

### Universal rules:
- universe/ is READ-ONLY for all agents. Never write to universe/.
- agents.yaml is READ-ONLY. Never modify agents.yaml.
- Always work with paths relative to the workspace root.

### State transitions:
Moving files between directories signals state changes.
After completing work, move files to the appropriate next-stage directory.
Commit to git after every meaningful state change.

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


Work on this specific spec: no-ephemeral-suggestions (currently in ready/)

--- no-ephemeral-suggestions.md ---
# no-ephemeral-suggestions

## 1. Overview

Agents surface workflow observations, friction points, architectural gaps, and improvement suggestions during their runs. Currently, these observations land in `memory/{agent}/needs.md` as flat entries with `category: observation` — either written by agents directly or extracted by the kernel safety net from response prose. Once in needs.md, observations have no severity classification, no lifecycle beyond open/resolved, and no path into the build pipeline. They accumulate in a flat list that the operator must manually read via `factory needs`. The reviewer just surfaced three real findings (stale universe docs, missing GC pass, daily log gaps) — they reached needs.md, but nothing in the factory can act on them from there.

This spec replaces the dead-end `category: observation` path with a structured observation pipeline. A new `specs/factory-internal/` directory receives every observation as a dated, severity-tagged file. The kernel mediates all writes: it promotes needs.md observation entries and its own safety-net extractions into this directory automatically during the post-run pass. `factory status` displays the factory-internal queue. A new `factory triage` command lets the operator promote observations into the normal spec pipeline (`specs/inbox/`) or dismiss them. Nothing about workflow improvement stays ephemeral.

## 2. Behavioral Requirements

### Kernel safety-net extraction → factory-internal

1. When the kernel safety net (`extract_surfaced_observations`) detects observations in agent response prose, it writes them as structured files to `specs/factory-internal/` instead of appending to `memory/{agent}/needs.md`. Each file follows the naming convention `{YYYY-MM-DDTHHMM}-{severity}-{slug}.md` (e.g., `2026-02-25T0817-low-decisions-gc-gap.md`). The datetime uses the extraction timestamp. The slug is derived from the observation text (kebab-case, max 50 chars). Default severity for kernel-extracted observations is `low`.

2. The existing kernel extraction logic (signal-phrase scanning, 3-observation cap, deduplication against agent-written needs) is preserved. The only change is the output destination and format.

### Kernel post-run promotion: needs.md observations → factory-internal

3. After each agent run, the kernel checks `memory/{agent}/needs.md` for any entries with `category: observation` and `status: open`. For each such entry, the kernel creates a corresponding file in `specs/factory-internal/`, then updates the needs.md entry to `status: promoted` with a `- promoted_to: {filename}` field. This runs after the safety-net pass (requirement 1) and before the GC passes.

4. When promoting a needs.md observation, the kernel assigns severity using keyword heuristics on the observation's `blocked` field:
   - `critical`: contains terms such as "pipeline blocked", "data loss", "governance gap", "security", "breaks", "cannot proceed", "integrity"
   - `high`: contains terms such as "friction", "gap", "missing", "stale", "incorrect", "degrades", "not firing", "accumulate"
   - `low`: everything else (improvement ideas, cosmetic suggestions, nice-to-haves)

   These heuristics provide a starting classification. The operator can reclassify by editing the file's `severity` field.

5. The kernel deduplicates before creating a factory-internal file: if `specs/factory-internal/` already contains an `open` file whose `## Observation` text matches the incoming observation (normalized whitespace comparison of the first 200 characters), skip creation and log a deduplication notice. This prevents repeated agent runs from creating duplicate observations.

### Factory-internal spec format

6. Each file in `specs/factory-internal/` follows this format:

   ```markdown
   # {slug}
   - severity: {critical|high|low}
   - status: {open|promoted|dismissed}
   - created: {ISO 8601 timestamp}
   - source-agent: {agent name}
   - source-type: {kernel-extraction|needs-promotion}

   ## Observation
   {The observation text — what was noticed, what the friction is, what might improve}

   ## Context
   {Which run, which task, what triggered the observation. For needs-promotion, includes the original needs.md entry ID.}
   ```

   When `status` is `promoted`, the file also contains:
   ```
   - promoted_to: specs/inbox/{slug}.md
   - promoted_at: {ISO 8601 timestamp}
   ```

   When `status` is `dismissed`, the file also contains:
   ```
   - dismissed_reason: {operator-provided reason}
   - dismissed_at: {ISO 8601 timestamp}
   ```

### Operator triage

7. `factory triage` provides lifecycle management for factory-internal observations:

   - `factory triage --list` — lists all `open` factory-internal specs, sorted by severity (critical → high → low) then age (oldest first). Shows filename, severity, source agent, age, and first line of the observation.
   - `factory triage --list --all` — includes `promoted` and `dismissed` entries.
   - `factory triage {filename} --promote` — creates a raw intent file at `specs/inbox/{slug}.md` containing the observation text (formatted as a "What I'm Seeing / What I Want to See" intent if the original text supports it, otherwise as-is). Updates the factory-internal file's `status` to `promoted` with `promoted_to` and `promoted_at` fields. Commits.
   - `factory triage {filename} --dismiss --reason "..."` — updates the factory-internal file's `status` to `dismissed` with `dismissed_reason` and `dismissed_at` fields. Commits.
   - `factory triage {filename}` with no action flag — displays the full observation content and available actions (promote/dismiss). Does not prompt interactively.

8. The `{filename}` argument accepts either the full filename (e.g., `2026-02-25T0817-low-decisions-gc-gap.md`) or just the slug portion (`decisions-gc-gap`). If the slug matches multiple files, the command prints all matches and exits with code 1.

### Pipeline integration

9. `factory status` includes a "Factory Internal" section when there are open observations. It appears after the pipeline section:
   ```
   Factory Internal (3 open):
     ▸ critical   1   stale-universe-docs
     ▸ high       2   decisions-gc-gap, daily-log-gaps
   ```
   Severity levels with zero open items are omitted. The entire section is omitted when there are zero open factory-internal observations.

10. The pipeline next-step hints include triage guidance when factory-internal specs exist with `critical` severity:
    ```
    → factory triage {filename} --promote
    ```
    `high` and `low` severity observations do not generate next-step hints — they are visible in the status section but do not compete with pipeline actions.

### Migration

11. On the first `factory run` or `factory status` invocation after this feature ships, the kernel runs a one-time migration: it reads all open `category: observation` entries across all `memory/*/needs.md` files, creates corresponding factory-internal specs, and marks the needs.md entries as `status: promoted`. The migration is idempotent — it skips entries already marked `promoted`. A migration marker file (`specs/factory-internal/.migrated`) prevents re-running on subsequent invocations.

### Skill updates

12. The `human-action-needed` skill (skills/shared/human-action-needed/SKILL.md) is updated:
    - The `observation` category description changes from "Non-blocking feedback during a reflection pass" to "Non-blocking feedback — kernel automatically promotes to `specs/factory-internal/` for structured triage."
    - No change to the writing instructions — agents continue writing `category: observation` entries to `memory/{agent}/needs.md`. The kernel handles promotion.
    - The "After Writing" section adds: "Observations are automatically promoted to `specs/factory-internal/` by the kernel post-run pass and triaged by the operator via `factory triage`."

13. The `self-improvement` skill (skills/shared/self-improvement/SKILL.md) step 3 is updated to note that observations written to needs.md are automatically promoted to factory-internal specs by the kernel. No change to agent behavior — the skill change is informational.

### GC integration

14. A new `cleanup-factory-internal` GC pass runs alongside the existing three GC passes. It removes factory-internal files whose status is `promoted` and whose `promoted_to` spec has been archived (exists in `specs/archive/`), or whose status is `dismissed` and whose `dismissed_at` is older than 30 days. This prevents unbounded accumulation.

### `factory needs` changes

15. `factory needs` no longer displays `category: observation` entries (they are now handled by `factory triage`). The observation count in `factory status` moves from the needs section to the factory-internal section. The `--blockers-only` flag becomes unnecessary for filtering observations since observations are no longer in the needs system — but the flag is retained for backward compatibility (it becomes a no-op for observation filtering).

## 3. Interface Boundaries

### Directory: `specs/factory-internal/`

New directory. Contains zero or more markdown files following the naming convention in requirement 1. Files are created by the kernel (not by agents directly — agents lack write access to this directory). The `.migrated` marker file is a zero-byte sentinel.

### CLI: `factory triage`

```
factory triage --list [--all]
factory triage {filename|slug} --promote
factory triage {filename|slug} --dismiss --reason "..."
factory triage {filename|slug}

  Manage factory-internal observations.

  Options:
    --list            List open observations (default sort: severity then age)
    --all             Include promoted and dismissed entries (with --list)
    --promote         Move observation to specs/inbox/ for pipeline processing
    --dismiss         Mark observation as dismissed (requires --reason)
    --reason "..."    Reason for dismissal (required with --dismiss)

  Exit codes:
    0   Success
    1   Slug matches multiple files, or file not found, or --dismiss without --reason
```

### Modified: `factory status`

Adds a "Factory Internal" section between pipeline and needs. Shows counts by severity with filenames.

### Modified: `factory needs`

Observation entries no longer appear in output. Observation count removed from the needs summary. The `--blockers-only` flag is retained but observation filtering is moot.

### Modified: `extract_surfaced_observations()` in `cli.py`

Output destination changes from `memory/{agent}/needs.md` to `specs/factory-internal/`. Return type and signal-phrase logic unchanged.

### File: `memory/{agent}/needs.md`

Existing `category: observation` entries gain a new status value `promoted` and a `promoted_to` field when the kernel promotes them. No other format changes.

### File: `specs/factory-internal/.migrated`

Zero-byte sentinel. Presence indicates the one-time migration (requirement 11) has completed.

## 4. Constraints

- **No `agents.yaml` changes.** The kernel (which has full filesystem access) creates all files in `specs/factory-internal/`. Agents continue writing to `memory/{agent}/needs.md` (which they already have access to). The kernel promotion pass bridges the access boundary.
- **Needs.md entries are never deleted by the kernel.** Promotion changes `status: open` to `status: promoted` and adds metadata. The full history persists.
- **Factory-internal files are never deleted by agents.** Only the kernel GC pass (requirement 14) removes files, and only when lifecycle criteria are met.
- **Severity heuristics are keyword-based, not semantic.** The kernel does not interpret observation meaning — it pattern-matches against the keyword lists in requirement 4. Misclassification is expected and acceptable; the operator can reclassify.
- **The deduplication check (requirement 5) uses text prefix comparison, not semantic similarity.** Two observations about the same issue phrased differently will not be deduplicated. This is acceptable — the operator can dismiss duplicates during triage.
- **The `factory triage --promote` command creates a raw intent in `specs/inbox/`, not a finished NLSpec.** The intent enters the normal pipeline: spec agent picks it up, drafts a full NLSpec, and promotes to `specs/ready/`.
- **The kernel post-run promotion pass (requirement 3) runs for every agent, not just specific ones.** Any agent that writes a `category: observation` entry to its needs.md will have it promoted.

## 5. Out of Scope

- **Semantic deduplication.** Detecting that two differently-worded observations describe the same issue. The operator handles this during triage.
- **Automatic promotion to specs/inbox/.** All factory-internal observations require explicit operator action (`factory triage --promote`) to enter the pipeline. No observation auto-promotes based on severity or age.
- **Agent-assigned severity.** Agents do not assign severity when writing to needs.md. The kernel assigns severity during promotion. If agents need to influence severity, they can include keywords from the heuristic list in their observation text.
- **Priority ranking beyond severity + age.** No upvote mechanism, no cross-agent endorsement.
- **Notification for factory-internal observations.** The existing WhatsApp notification after agent runs already includes a summary. No separate notification channel for observations.
- **Retroactive extraction from historical agent responses.** The migration (requirement 11) handles existing needs.md entries. Past agent responses that were never extracted are not re-scanned.

## 6. Verification Criteria

- After an agent run where the kernel safety net detects observations in response prose, files appear in `specs/factory-internal/` with correct naming convention, severity, format, and `source-type: kernel-extraction`.
- After an agent run where the agent wrote a `category: observation` entry to its `needs.md`, the entry's status changes to `promoted` with a `promoted_to` field, and a corresponding file exists in `specs/factory-internal/` with `source-type: needs-promotion`.
- `factory status` shows a "Factory Internal" section with severity-grouped counts when open observations exist, and omits the section when none exist.
- `factory triage --list` displays open observations sorted by severity then age, with filename, source agent, age, and observation summary.
- `factory triage {file} --promote` creates a file in `specs/inbox/`, updates the factory-internal file to `status: promoted`, and commits. The promoted observation no longer appears in `factory triage --list` but appears in `factory triage --list --all`.
- `factory triage {file} --dismiss --reason "not actionable"` updates the factory-internal file to `status: dismissed` with the reason, and commits.
- `factory needs` no longer shows observation entries — only blocker categories (permission-change, config-edit, manual-intervention, approval).
- The one-time migration converts existing open observation entries in `memory/*/needs.md` to factory-internal specs and marks them as promoted.
- The `cleanup-factory-internal` GC pass removes promoted files whose corresponding inbox spec has been archived, and dismissed files older than 30 days.

## 7. Ambiguities

### 7.1 Severity heuristic vs agent-controlled severity
- reversibility: high
- impact: implementation
- status: auto-resolved

**Options:**
- **(a)** Kernel assigns severity via keyword heuristics (as specced in §2.4). Agents influence severity indirectly through word choice.
- **(b)** Add a `severity` field to the needs.md observation format so agents can explicitly assign severity. Kernel uses agent-assigned severity when present, falls back to heuristics.

**Resolution:** Auto-resolved to **(a)**. Keeping severity assignment in the kernel avoids changes to the needs.md format and the human-action-needed skill's entry format. The operator can reclassify after the fact. If agent-assigned severity proves necessary, adding a `severity` field to needs.md is backward-compatible — the kernel promotion pass can check for it and prefer it over heuristics.

### 7.2 Write access model
- reversibility: high
- impact: implementation
- status: auto-resolved

**Options:**
- **(a)** Kernel-mediated: agents write to needs.md (existing access), kernel promotes to `specs/factory-internal/`. No agents.yaml changes.
- **(b)** Direct writes: add `specs/factory-internal/` to all agents' `can_write` in agents.yaml. Update skills to teach direct writing.

**Resolution:** Auto-resolved to **(a)**. Preserves existing access model. The kernel already runs after every agent and has full filesystem access. Adding write permissions for all 7 agents is a governance change that adds complexity without proportional benefit. The promotion delay (end of agent run) is negligible.

