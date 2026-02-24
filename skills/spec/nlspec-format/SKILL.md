---
name: nlspec-format
description: How to write a natural language specification that Builder can implement without asking questions.
---

## Structure of an NLSpec

### 1. Overview (1-2 paragraphs)
What this project/feature is and why it exists. Written for a human who might read this in 6 months.

### 2. Behavioral Requirements
What the system DOES, described as observable behaviors. Not implementation details.
Format: "When [trigger], the system [behavior], resulting in [observable outcome]."

### 3. Interface Boundaries
Every point where the system touches the outside world:
- CLI arguments/flags (with exact syntax)
- API endpoints (with request/response shapes)
- File formats (with examples)
- Environment variables
- Dependencies on external services

### 4. Constraints
What the system must NOT do. Error cases. Security boundaries. Performance requirements.
Be explicit about edge cases — these are where Builder most often goes wrong.

### 5. Out of Scope
Explicitly state what this spec does NOT cover. This prevents Builder from gold-plating.

### 6. Verification Criteria
How Verifier should know this works. Not test cases (those are holdout scenarios), but observable properties: "A user should be able to [action] and see [result]."

### 7. Ambiguities (if any)
When a spec has open questions that block promotion to `specs/ready/`, write them as structured entries. Each ambiguity must be tagged for the kernel's Decision Monitor to classify and route:

```markdown
### 7.N {short-description}
- reversibility: high | low
- impact: governance | implementation | cosmetic
- status: open

**Options:**
- **(a)** {option description}
- **(b)** {option description}

**Recommendation:** {your recommendation, if any}
```

The kernel reads these tags after the spec run:
- `reversibility: high` + `impact: implementation|cosmetic` → auto-resolved (soft gate)
- `reversibility: low` OR `impact: governance` → blocks for operator (hard gate)

Do not write ambiguities as unstructured prose. The structured format is what makes the Decision Monitor work.

## The Quality Test

A spec is ready when you can hand it to a competent developer who has never heard of this project and they can build it without asking a single question. If they'd need to ask, the spec is underspecified.

## Using Researcher

Before speccing anything non-trivial, write a research request: "I need to spec a system that does X. What are the established approaches? What are the key design decisions?" Wait for the brief. Then spec with informed constraints.
