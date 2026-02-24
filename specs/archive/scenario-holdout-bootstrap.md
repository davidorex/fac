# NLSpec: Scenario Holdout Bootstrap

## Overview

The factory's trust model depends on scenario holdouts — verification criteria that Builder never sees but Verifier evaluates against. The blueprint defines scenario holdouts as foundational (Step 2 of the bootstrap sequence) and the Verifier's protocol includes scenario evaluation as explicit steps (5-6). However, `scenarios/` is empty: no meta-scenario exists, no per-project scenarios have been written, and no verification report has ever included scenario evaluation.

This spec makes the scenario holdout system operational by providing CLI scaffolding tools, the meta-scenario content from the blueprint, and proposed skills for scenario authoring and verification integration. The runtime creates files and directories; the human writes actual scenario content.

## Behavioral Requirements

### Meta-scenario initialization

When the human runs `factory scenario init-meta`, the runtime creates `scenarios/meta/factory-itself.md` with the meta-scenario content defined below, resulting in a file Verifier can reference during any factory infrastructure verification.

When the file already exists, the command prints its path and a message indicating it already exists, resulting in no file modification (idempotent — preserves human edits).

### Per-project scenario scaffolding

When the human runs `factory scenario new {project-name}`, the runtime creates `scenarios/{project-name}/` and writes `scenarios/{project-name}/_template.md` with the template content defined below, resulting in a directory structure ready for the human to add scenario files.

When the directory already exists, the command prints a message indicating it already exists and does not overwrite any files. When the directory exists but `_template.md` is missing, the command writes `_template.md` only.

### Scenario listing

When the human runs `factory scenario list`, the runtime reads all directories under `scenarios/`, counts `.md` files per directory (excluding `_template.md` and `satisfaction.md`), and displays a table showing: directory name (with `[meta]` label for `scenarios/meta/`), scenario count, and whether `satisfaction.md` exists (with its modification date if present).

When `scenarios/` is empty or does not exist, the command prints "No scenario directories found. Run `factory scenario init-meta` to create the meta-scenario."

### Status integration

When the human runs `factory status`, the output includes a "Scenario Coverage" section after the existing sections. This section shows the total number of scenario directories, total scenario files, and a warning line if any task in `tasks/review/` or `tasks/verified/` exists while `scenarios/meta/factory-itself.md` does not.

### Pre-verification warning

When the runtime invokes Verifier for a task and `scenarios/meta/factory-itself.md` does not exist, the runtime logs a warning: "No scenario holdouts found. Verification will be spec-matching only. Run `factory scenario init-meta` to create the meta-scenario."

When `scenarios/meta/factory-itself.md` exists, no warning is logged. The warning is informational — it does not block or alter the verification flow.

### Proposed skills

When building this spec, Builder writes two skill files to `skills/proposed/`:

**`skills/proposed/scenario-authoring-guide/SKILL.md`** — Guidance for the human on when and how to write scenario holdouts:
- Write scenarios BEFORE or ALONGSIDE specs, not after implementation
- 2-5 scenarios per project (cover major user paths without becoming a test suite)
- Write from the user's perspective, not the developer's
- Focus on the non-obvious: edge cases, error recovery, interaction patterns the spec might not make explicit
- Scenarios MUST NOT be shared with Builder — holdout by design
- For factory infrastructure work, evaluate against `scenarios/meta/factory-itself.md` directionally (does this change move the factory closer to the meta-scenario?)
- Skill must be under 40 lines total

**`skills/proposed/verification-with-scenarios/SKILL.md`** — Guidance for Verifier on integrating scenario evaluation into verification reports:
- Verification report gains a `## Scenario Evaluation` section after the spec-matching section
- For each scenario file found in `scenarios/{project}/`: state the scenario title, describe how the implementation handles it, judge whether it satisfies the scenario
- If no scenarios exist for the project: include the section with "No scenario holdouts found for this project"
- Scenario evaluation contributes to but does not solely determine the satisfaction score
- Failed scenarios described with the same specificity as failed spec requirements
- For the meta-scenario: evaluate directionally (closer to or further from the North Star), not pass/fail
- Skill must be under 40 lines total

## Interface Boundaries

### CLI commands

```
factory scenario init-meta
  Creates: scenarios/meta/factory-itself.md
  Stdout: "Created scenarios/meta/factory-itself.md" | "Already exists: scenarios/meta/factory-itself.md"
  Exit code: 0 in both cases

factory scenario new <project-name>
  Creates: scenarios/<project-name>/_template.md
  Stdout: "Created scenarios/<project-name>/_template.md" | "Already exists: scenarios/<project-name>/"
  Exit code: 0 in both cases
  Validation: project-name must match [a-z0-9][a-z0-9_-]* (lowercase, hyphens, underscores, no leading special chars)
  Exit code: 1 with error message if project-name is invalid

factory scenario list
  Stdout: formatted table
  Columns: Name, Scenarios, Satisfaction
  Example:
    Name                 Scenarios    Satisfaction
    meta [meta]          1            —
    my-cli-tool          3            ✓ (2026-02-20)
    other-project        0            —
  Exit code: 0
```

### Meta-scenario file content

The content of `scenarios/meta/factory-itself.md`:

```markdown
# Factory Meta-Scenario

A solo developer with a new project idea should be able to describe it in 2-3 sentences, leave, and come back to find: a complete NLSpec they can review, a working implementation, a verification assessment, and a list of what the system learned from building it. The developer's only job is to approve the spec and approve the final result. Everything in between is the factory's problem.

## Evaluation Guidance

This is a directional criterion, not a pass/fail gate. The factory is not yet at meta-scenario fulfillment. When evaluating factory infrastructure changes, ask: does this change move the factory closer to or further from this scenario?

- Closer: changes that increase pipeline autonomy, improve reliability, strengthen self-correction, reduce required human intervention for routine operations
- Further: changes that add manual steps, create ambiguity in the pipeline, lose information between stages, or require human expertise to interpret agent output

Each factory infrastructure task should be evaluated for directional alignment. Document the reasoning.

## Source

Blueprint line 586-589: "Write this into `scenarios/meta/factory-itself.md` on day one."
```

### Scenario template file content

The content of `scenarios/{project-name}/_template.md`:

```markdown
# Scenario: [Title]

<!-- Copy this file for each scenario. Name copies scenario-001.md, scenario-002.md, etc. -->
<!-- Delete this _template.md file or leave it — it is excluded from scenario counts. -->

## User Story

[Describe a specific end-to-end user interaction. Who is the user? What do they want to accomplish? What do they do step by step? What do they see at each step?]

## Expected Behavior

[Describe the observable outcomes. What should happen at each step? Include both the happy path and edge cases this scenario tests.]

## Why This Matters

[What aspect of the spec does this scenario stress-test? What could go wrong if this scenario fails? What would a user feel if this scenario broke?]
```

### File system effects

```
scenarios/
├── meta/
│   └── factory-itself.md          # Created by: factory scenario init-meta
└── {project-name}/
    └── _template.md               # Created by: factory scenario new {project-name}

skills/
└── proposed/
    ├── scenario-authoring-guide/
    │   └── SKILL.md               # Created by Builder during build
    └── verification-with-scenarios/
        └── SKILL.md               # Created by Builder during build
```

## Constraints

- Builder CANNOT read `scenarios/`. The runtime code Builder writes creates files there, but Builder cannot read them back for verification. Verifier handles verification of scenario file contents.
- The meta-scenario text is hardcoded in the runtime source — not loaded from `universe/` at runtime. This avoids a runtime dependency on universe file structure.
- `_template.md` files are reference only. No agent generates actual scenario content. Scenarios are always human-authored.
- `factory scenario` commands are subcommands of the existing `factory` CLI, following the same patterns as `factory status`, `factory needs`, `factory cleanup-specs`, etc.
- The pre-verification warning is logged via the runtime's existing logging mechanism — no new logging infrastructure.
- Proposed skills are under 40 lines each. This is a hard limit from the seed-skill-gaps convention.
- `factory scenario init-meta` creates the `scenarios/meta/` directory if it does not already exist (it may or may not exist from the initial workspace bootstrap).

## Out of Scope

- Automated scenario generation. Scenarios are human-authored holdouts — automation would defeat their purpose.
- Scenario versioning beyond git. Git already tracks scenario file changes.
- Modifying the existing `verification-protocol` skill in `skills/verifier/`. Librarian handles skill promotion; this spec only proposes new skills to `skills/proposed/`.
- Running scenarios as automated tests. Scenarios are evaluated by Verifier's judgment, not programmatic execution.
- Task-to-project mapping for per-project scenario lookup. All current factory work is infrastructure evaluated against `scenarios/meta/`. Per-project scenario routing activates when `projects/` has real software projects — that is a future spec.
- Creating actual scenario content beyond the meta-scenario. The human writes scenarios.

## Verification Criteria

- `factory scenario init-meta` creates `scenarios/meta/factory-itself.md` with content matching the meta-scenario text above. Running it again does not modify the file.
- `factory scenario new test-project` creates `scenarios/test-project/_template.md` with content matching the template above. Running it again does not overwrite.
- `factory scenario new INVALID!NAME` exits with code 1 and an error message.
- `factory scenario list` displays a table with accurate directory names and file counts. When no directories exist, displays the help message.
- `factory status` includes a Scenario Coverage section.
- `skills/proposed/scenario-authoring-guide/SKILL.md` exists and is under 40 lines.
- `skills/proposed/verification-with-scenarios/SKILL.md` exists and is under 40 lines.
- The pre-verification warning appears in runtime log output when `scenarios/meta/factory-itself.md` is absent during a verification invocation.
