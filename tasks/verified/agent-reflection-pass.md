# Verification: agent-reflection-pass

spec: specs/archive/agent-reflection-pass.md
review: tasks/review/agent-reflection-pass.md
verified: 2026-02-24T20:36:00
score: 9/10

## Satisfaction Score: 9/10

High-quality implementation. All 12 behavioral requirements satisfied. Two proposed skills are well-formed and faithful to spec. Minor issues identified are non-blocking and within acceptable tolerances.

## Criterion-by-Criterion Assessment

### 1. `factory reflect` invokes all 7 agents in pipeline order — PASS
`PIPELINE_ORDER` constant defines `[researcher, spec, builder, verifier, librarian, operator, reviewer]`. The `reflect` command iterates this list, filtered to agents present in config. Sequential invocation via `run_agent()` with `is_heartbeat=False`.

### 2. `factory reflect {agent-name}` single-agent and error handling — PASS
Single agent path: `agents_to_run = [agent_name]`. Unknown agent: `sys.exit(1)` with `Unknown agent: {agent_name}`. Matches spec exactly.

### 3. Same invocation mechanism as heartbeat, with reflection prompt — PASS
Uses the same `run_agent()` function with `config` and `agent_cfg`. Agent gets its full system prompt (identity, always-loaded skills, access scopes, memory) plus the reflection prompt as the message. `is_heartbeat=False` ensures the heartbeat message is not appended.

### 4. Runtime extracts agent's own YAML block — PASS
`_agent_yaml_block()` re-reads `agents.yaml`, extracts the named agent's section, serializes via `yaml.dump()`. Clean function, no side effects.

### 5. Reflection prompt matches spec template — PASS
Prompt structure matches: opening paragraph → YAML block in `---` delimiters → skill loading instruction → observation writing instruction → NO_REPLY instruction. The implementation adds the agent-reflection skill content inline between the YAML block and the instruction (when the file exists in shared), which is additive rather than substitutive.

### 6. Post-reflection summary with delta count — PASS
`_snapshot_needs_ids()` captures entry IDs before and after. `len(post_ids - pre_ids)` computes new entries. Summary format matches spec: `Reflection complete — {N} agents ran, {M} new observations written.` The "Run `factory needs` to review." footer is conditionally shown only when `new_count > 0` — minor deviation from spec template but sensible (no value in suggesting review when nothing was written).

### 7. Failed agents don't abort; summary includes failure detail — PASS
Exception handler catches failures per-agent, appends to `failed` list, continues loop. Summary includes failure detail: `(N failed: name1, name2)`. Exit code 2 only when `n_ran == 0` (all failed). Matches spec exactly.

### 8. `observation` category added — PASS
The `_OBSERVATION_CATEGORY = "observation"` constant is used to separate observation entries from blocker entries in display logic. The proposed human-action-needed skill adds `observation` to the categories table.

### 9. `factory needs` displays observations in separate section — PASS
Lines 1420-1424: observations are displayed in an `Observations (N):` section below all blocker categories, using the same `_print_entry()` helper. Display format matches spec's example.

### 10. `factory needs --blockers-only` excludes observations — PASS
`--blockers-only` flag (Click option) gates the observation section display at line 1420: `if not blockers_only and observation_entries:`. Blocker categories are always shown.

### 11. Proposed agent-reflection skill — PASS
57 lines (under 150-line limit). Covers all 8 "what to examine" areas from spec (role, skills, access, daily logs, private memory, pipeline inputs, pipeline outputs, learnings). Covers observation writing format with deduplication. Covers all "what NOT to do" items. Content quality is good.

### 12. Updated human-action-needed skill — PASS
53 lines. Adds `observation` row to categories table (5th row, existing 4 preserved). Adds observation guidance to "When to Write" section. Updates field descriptions to accommodate non-blocking observations ("what you cannot do, or what friction you observe"). Adds `--blockers-only` mention to "After Writing" section.

## Minor Observations (Non-Blocking)

1. **Skill inline path dependency**: The code looks for `skills/shared/agent-reflection/SKILL.md` to inline content. The skill is currently at `skills/proposed/` awaiting Librarian promotion. Until promoted, agents receive the reflection prompt without inline skill content — they'll see "Load the `shared/agent-reflection` skill" but the content won't be embedded. The `if exists()` guard degrades gracefully. This is the normal factory lifecycle, not a bug.

2. **`--blockers-only` header count includes observations**: When `--blockers-only` is set, the "Factory Needs — N open items" header count includes observation entries that are then suppressed from display. Builder flagged this in review notes as within spec. Technically correct (the spec says to exclude observations from display, not to adjust the count), but creates a UX where the count doesn't match visible entries. This is an improvement opportunity, not a spec violation.

3. **Agent-reflection skill line 57 wording**: "Do not write NO_REPLY if you have nothing to observe — absence of friction is fine but needs no entry; write NO_REPLY and stop." The sentence contradicts itself (opens with "Do not write NO_REPLY," ends with "write NO_REPLY and stop"). The intent is clear (don't create a needs entry, do write NO_REPLY), but the wording is garbled. The spec's own bullet on this topic is similarly ambiguous. The Librarian may want to clean this up during promotion review.

## Scenario Evaluation

### Meta-Scenario: Directional Alignment
`factory reflect` moves the factory **closer** to the meta-scenario. It strengthens self-correction by giving agents a structured introspection mechanism. Instead of relying solely on the reviewer's external view, each agent can surface friction from its own position in the pipeline. This reduces the human's need to manually diagnose agent misalignment — agents surface it themselves. The observation category extends the needs.md channel from "I'm blocked" to "I notice something," which is a meaningful capability expansion for factory autonomy.

### No Task-Specific Holdout Scenarios
No holdout scenarios exist specifically for `agent-reflection-pass`. The implementation could be further stress-tested by scenarios like: "What happens when an agent's reflection triggers a permission-change need?" or "What happens when factory reflect is interrupted mid-pass?" These are verification gaps the factory should close in future scenario authoring.

## Verification Gaps (Factory Needs)

- **No integration test**: The reflect command hasn't been exercised end-to-end against live agents. Code analysis confirms structural correctness, but the actual agent behavior during reflection (quality of observations, deduplication in practice, NO_REPLY behavior) is unverified.
- **Missing scenarios**: No holdout scenarios for the reflection pass. Scenarios covering partial failure, observation deduplication across multiple reflection passes, and interaction between `--blockers-only` and observation-only needs states would strengthen future verification.
