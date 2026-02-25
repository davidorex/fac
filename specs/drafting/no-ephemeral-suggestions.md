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
