# agent-reflection-pass

## Overview

Every agent has "Your voice matters" in its role description and `shared/human-action-needed` in its available skills. The channel exists (`memory/{agent}/needs.md`) and the aggregation tool exists (`factory needs`). But no mechanism actively triggers agents to use it for anything beyond blockers encountered during normal work. The needs.md system is reactive — agents write entries when they hit walls, not when they notice friction, misalignment, or improvement opportunities.

This spec adds `factory reflect` — a CLI command that invokes each agent (or a specified agent) with a reflection-oriented prompt. During a reflection pass, the agent examines its own configuration, memory, recent daily logs, the pipeline stages it interacts with, and the learnings directory. It writes structured observations to `memory/{agent}/needs.md` using an expanded category set that includes non-blocking feedback alongside the existing blocker categories.

The human runs `factory reflect` when they want the factory to look at itself from the inside. This complements the reviewer's external view — the reviewer looks at the system holistically; reflection asks each agent what it sees from its own position in the pipeline.

## Behavioral Requirements

### The `factory reflect` command

1. **`factory reflect` invokes every agent defined in `agents.yaml` with a reflection prompt.** Each agent is invoked sequentially (not in parallel). The invocation order follows the pipeline: researcher, spec, builder, verifier, librarian, operator, reviewer.

2. **`factory reflect {agent-name}` invokes only the named agent.** If the name does not match any agent in `agents.yaml`, the command exits with code 1 and prints: `Unknown agent: {agent-name}`.

3. **The runtime invokes each agent using the same mechanism as heartbeat invocation** (same model, same skills, same access scopes), but with the reflection prompt appended to the agent's normal context instead of the heartbeat prompt. The agent's `always` skills are loaded. Additionally, the runtime loads `shared/agent-reflection` as an extra skill for the duration of the reflection invocation.

4. **The runtime extracts the agent's own definition from `agents.yaml`** and includes it as literal text in the reflection prompt. This gives the agent visibility into its own role description, skills list, access scopes, heartbeat schedule, model, and shell access — without requiring the agent to have read access to `agents.yaml` (which is READ-ONLY for all agents).

5. **The reflection prompt sent to each agent is:**
   ```
   This is a reflection pass, not a heartbeat. You are being asked to examine yourself — your configuration, your recent work, your place in the pipeline — and surface observations for the human.

   Your current configuration from agents.yaml:
   ---
   {agent's full YAML block from agents.yaml}
   ---

   Load the `shared/agent-reflection` skill and follow its instructions. Write your observations to memory/{agent}/needs.md using the human-action-needed format with the appropriate category. If you have nothing to observe, write NO_REPLY and exit.
   ```

6. **After all agents complete, the runtime prints a summary:**
   ```
   Reflection complete — {N} agents ran, {M} new observations written.

   Run `factory needs` to review.
   ```
   The count of new observations (`M`) is determined by comparing the state of all `memory/*/needs.md` files before and after the reflection pass (new entries that were not present before).

7. **If an agent's invocation fails (runtime error, timeout, model error), the runtime logs the failure and continues to the next agent.** It does not abort the entire reflection pass. The summary includes failed agents:
   ```
   Reflection complete — 7 agents ran (1 failed: operator), 4 new observations written.
   ```

### Extended needs.md categories

8. **A new category `observation` is added to the needs.md format.** Observations are non-blocking feedback — things the agent notices that could improve the factory but are not preventing it from doing its current work. The existing 4 categories (`permission-change`, `config-edit`, `manual-intervention`, `approval`) remain unchanged. The `observation` category covers:
   - Skills that are missing, stale, or misaligned with actual work
   - Access scopes that seem too narrow or too broad based on the agent's experience
   - Role description language that doesn't match what the agent actually does
   - Friction patterns across multiple runs (repeated workarounds, recurring NO_REPLY due to empty pipelines, etc.)
   - Suggestions for factory-level improvements (new conventions, new skills, process changes)

9. **`factory needs` displays `observation` entries in a separate section below the existing blocker categories.** The display format for observations:
   ```
   Observations (3):
     spec-drafting-delete-friction             [spec, 1d ago]
       Every spec cycle leaves stale copies in drafting/ — cleanup skill would help
     builder-shell-access-underused            [builder, 1d ago]
       Full shell access granted but never used for anything beyond git — could be read_only
     verifier-scenario-dir-empty               [verifier, 1d ago]
       scenarios/ has been empty for all 12 verification runs — holdout evaluation is inoperative
   ```

10. **`factory needs --blockers-only` displays only the original 4 categories** (permission-change, config-edit, manual-intervention, approval), excluding observations. This allows the human to focus on actionable blockers when observations are noisy.

### Proposed skill: `shared/agent-reflection`

11. **Builder produces a proposed skill at `skills/proposed/agent-reflection/SKILL.md`** that teaches agents what to examine during a reflection pass and how to write observations. The skill covers:

    - **What to examine:**
      - Your role description: does it accurately describe what you do? Is anything missing or misleading?
      - Your skills list: which skills do you actually use? Are any missing? Are any loaded but never activated?
      - Your access scopes: have you ever needed to read or write something outside your current scopes? Have you been granted access to directories you never touch?
      - Your recent daily logs (last 7 days or last 5 entries, whichever is fewer): what patterns emerge? Repeated NO_REPLY? Recurring blockers? Repeated workarounds?
      - Your private memory: is it accurate and current? Is anything missing that you keep rediscovering?
      - Your pipeline inputs (directories you read from): are they consistently populated? Is anything stale?
      - Your pipeline outputs (directories you write to): is your output format working well for downstream agents?
      - The learnings directory: are there learnings relevant to your work that haven't been incorporated into your skills?

    - **How to write observations:**
      - Use the `human-action-needed` format (requirement 2 of the human-action-report spec)
      - Use `category: observation` for non-blocking feedback
      - Use the existing categories (`permission-change`, `config-edit`, etc.) if the reflection surfaces an actual blocker
      - The `blocked` field for observations should describe the friction or misalignment, not an inability to work
      - The `### Exact Change` section for observations should describe the suggested improvement, even if the agent isn't certain it's the right fix
      - Apply the standard deduplication check: don't create an entry if an open one with the same ID already exists

    - **What NOT to do:**
      - Don't generate observations about other agents' fitness — only your own
      - Don't generate intents (that's the reviewer's job) — observations are feedback, not specs
      - Don't reflect on the reflection mechanism itself — meta-recursion is the human's domain
      - Don't write NO_REPLY if you genuinely have nothing to observe — the absence of friction is itself informative, but doesn't need a needs entry

12. **Builder also produces an updated version of `skills/proposed/human-action-needed/SKILL.md`** that adds the `observation` category to the categories table. The update adds one row to the existing table and one sentence to the "When to Write" section noting that observations are written during reflection passes, not during normal heartbeat work.

## Interface Boundaries

### CLI: `factory reflect`

```
factory reflect [agent-name]

  Invokes agents with a reflection prompt. Agents examine their own
  configuration, memory, and pipeline state, then write observations
  to memory/{agent}/needs.md.

  Arguments:
    agent-name    Optional. Invoke only this agent. If omitted, all agents
                  are invoked sequentially in pipeline order.

  Exit codes:
    0   All invoked agents completed (some may have written NO_REPLY)
    1   Invalid agent name specified
    2   All invoked agents failed (none completed successfully)
```

### Extended `memory/{agent}/needs.md` entry format

The existing format from human-action-report is unchanged. The `observation` category is added as a valid value for the `category` field:

```markdown
## {agent}-{kebab-case-description}
- status: open
- created: {ISO 8601 timestamp}
- category: observation
- blocked: {description of friction, misalignment, or improvement opportunity}
- context: {what prompted this observation — reflection pass, pattern across runs, specific incident}

### Exact Change
{suggested improvement — may be a concrete change or a description of what should be different}
```

### Categories (updated)

| Category | Meaning |
|----------|---------|
| `permission-change` | Agent's `can_read` or `can_write` needs expansion |
| `config-edit` | A READ-ONLY config file needs modification |
| `manual-intervention` | One-time human action outside the codebase |
| `approval` | Agent has a proposed action requiring human sign-off |
| `observation` | Non-blocking feedback — friction, misalignment, or improvement opportunity |

## Constraints

- **No `agents.yaml` changes.** Reflection uses each agent's existing access scopes. The agent examines only what it can already read. If it discovers it needs broader access, that itself becomes a needs entry.
- **Sequential invocation only.** Agents reflect one at a time. No parallel invocation. This keeps API usage predictable and allows the human to interrupt (`Ctrl-C`) after any agent without losing work from completed agents.
- **No automatic trigger.** `factory reflect` is human-initiated only. It is not a heartbeat and is not scheduled. The human decides when reflection adds value.
- **Reflection does not replace the reviewer.** The reviewer generates improvement intents based on a holistic view of the factory. Reflection generates agent-specific observations based on an inward view. They are complementary. An agent's reflection output may inform the reviewer's next cycle, but there is no direct coupling.
- **Agents cannot see run history unless they already can.** No agent currently has `runs/` in `can_read`. Agents infer their recent performance from their own daily logs and the state of pipeline directories they interact with. If an agent determines it needs run history, it surfaces that as a needs entry.
- **The `observation` category does not trigger reviewer escalation.** Requirement 11 of the human-action-report spec says the reviewer escalates needs entries pending more than 2 review cycles. This escalation applies only to the original 4 blocker categories, not to observations. Observations are informational and may remain open indefinitely without escalation.

## Out of Scope

- **Automated action on observations.** Observations are surfaced to the human via `factory needs`. The human decides what to act on. No runtime mechanism auto-resolves observations or converts them to intents.
- **Reflection scheduling or periodicity.** The intent mentions no schedule, and this spec does not add one. The human runs `factory reflect` when they judge it useful — perhaps after a batch of work completes, after onboarding a new agent, or after a series of failures.
- **Cross-agent reflection.** Each agent reflects on itself only. An agent does not evaluate other agents' configurations or performance. That is the reviewer's domain.
- **Reflection depth configuration.** All agents get the same reflection prompt. There is no mechanism to ask for "deeper" or "shallower" reflection. The skill guides what to examine; the agent's judgment determines depth.
- **Filtering `factory needs` by source (heartbeat vs. reflection).** Needs entries written during reflection are indistinguishable from those written during normal work. Both use the same format. If source-tracking becomes valuable, it is a future extension (add a `source: reflection` or `source: heartbeat` field).

## Verification Criteria

- Running `factory reflect` invokes all 7 agents in pipeline order. Each agent receives the reflection prompt containing its own agents.yaml configuration block.
- Running `factory reflect spec` invokes only the spec agent. Running `factory reflect nonexistent` exits with code 1 and an error message.
- An agent that identifies friction during reflection writes a well-formed entry to `memory/{agent}/needs.md` with `category: observation` and all required fields.
- Running `factory needs` after a reflection pass displays observation entries in a separate "Observations" section below the blocker categories.
- Running `factory needs --blockers-only` excludes observation entries from the display.
- If an agent has nothing to observe, it writes NO_REPLY and exits cleanly. The summary count reflects this (the agent "ran" but wrote 0 new observations).
- If one agent fails during a reflection pass, the remaining agents still run and the summary indicates which agent failed.
- The proposed `skills/proposed/agent-reflection/SKILL.md` is a well-formed skill under 150 lines that covers what to examine and how to write observations.
- The updated `skills/proposed/human-action-needed/SKILL.md` adds the `observation` category without altering the existing 4 categories.
