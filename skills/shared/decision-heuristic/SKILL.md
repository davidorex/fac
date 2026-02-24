---
name: decision-heuristic
description: When blocked by ambiguity, choose the best reversible option, document the debt, and ship. Do not wait for perfect information. Do not build the minimal hack.
---

## Best Non-Minimal Decision Principle

When blocked by ambiguity, do not wait for perfect information. Do not build the minimal hack. Build the best non-minimal decision — the option that:

- Unblocks progress today
- Preserves optionality for tomorrow
- Can be refactored without breaking the world

## Process

1. **Classify the ambiguity.** Tag each open question:
   - `reversibility: high` — changing this decision later is bounded (one module, one config change, one interface swap)
   - `reversibility: low` — changing this decision later has cascading effects (governance policy, data format, public API)
   - `impact: governance` — affects access control, enforcement, trust boundaries
   - `impact: implementation` — affects how something is built, not what it does
   - `impact: cosmetic` — affects presentation, naming, or UX details

2. **Apply the routing rule:**
   - `reversibility: high` → soft gate. Agent resolves it: choose the more-flexible option, build the seam, document the trigger, proceed.
   - `reversibility: low` OR `impact: governance` → hard gate. Write a structured decision request. Pipeline blocks for the system operator.

3. **For soft gates — decide in 5 minutes of analysis, not 50:**
   - Choose the reversible path: if Option A locks you in and Option B doesn't, choose B even if A seems "better" today
   - Document the decision in builder-notes (see below)
   - Proceed: build it clean, build it testable, build it bounded

4. **For hard gates — write a structured decision request** to `tasks/decisions/{spec-name}.md`:

```markdown
## {section-id}: {short-description}
- status: awaiting-operator
- reversibility: low
- impact: governance
- context: {what you were doing when you hit this}

### Options
- **(a)** {option description}
- **(b)** {option description}
- **(c)** {option description}

### Recommendation
{your recommendation and reasoning, if you have one}
```

## Decision Documentation (builder-notes)

When an agent makes a decision under ambiguity (soft gate), document it:

```markdown
## {section-id}: {short-description}
- decision: {what was chosen}
- status: auto-resolved
- reversibility: high
- rationale: {why this option, in one sentence}
- seam: {where in the code the decision is parameterized}
- refactor-trigger: {condition under which this should be revisited}
- cost-to-change: low | medium | high
```

## The Heuristic

"If I change my mind tomorrow, how much breaks?" If the answer is "everything," this is a hard gate — stop and ask the operator. If the answer is "this one module," make the call and ship it.
