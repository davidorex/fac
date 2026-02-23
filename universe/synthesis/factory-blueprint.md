# The Factory That Makes Factories

## The Recursion

You want to build a local team of agents whose job is to start, continue, maintain, and extend software projects — including, eventually, themselves. This is the most honest version of the problem: the first factory the factory builds is a better version of itself.

That recursion isn't a cute observation. It's a design constraint. Every skill the agents learn building *other* projects feeds back into their ability to build factories. Every failure pattern they encounter in a Rails app or a CLI tool or a data pipeline is a learning that makes them better at growing the *next* project. The system is its own first customer.

---

## Six Roots. Infinite Branches.

Six persistent agents — the roots. But any agent can decompose: spin up temporary subagents beneath itself when a problem is too big, too multi-faceted, or would benefit from parallel exploration. The roots are the identities that persist. Everything below them is ephemeral — grown for a task, dissolved when done, learnings harvested by Librarian.

This means the "team" is never a fixed size. It's a tree that grows and prunes itself based on the work. On a quiet day it's six agents checking their heartbeats. On a complex project it might be six agents with fifteen subagents across them, some of those subagents running in parallel, all converging into their parent's context when done.

### 1. Researcher (The Scout)

**What it does:** Finds the best way to do things. When any agent hits a question that requires outside knowledge — what's the best library for this? How does this API actually work? What's the elegant solution to this class of problem? — Researcher goes and gets the answer. It searches, reads, evaluates options, and comes back with a recommendation that's specific enough to act on.

**Why it exists:** This is the agent that imports expertise from outside the factory walls. Spec needs to know what's *possible* before writing a spec. Builder needs to know the best approach before implementing. Verifier needs domain context to judge quality. Without Researcher, every agent reinvents wheels or makes decisions from partial knowledge.

**Where it sits in the flow:** Upstream and alongside everything. Spec calls on it during drafting: "I need to spec a real-time sync system — what are the established patterns?" Builder calls on it mid-implementation: "This concurrency model isn't working — what do experts recommend?" Verifier calls on it for domain calibration: "Is this the standard way to handle OAuth token refresh?"

**Why it decomposes most naturally:** A research question often has multiple facets. "What's the best approach to build X?" might mean: investigate three competing libraries, read their docs, compare their APIs, check their maintenance status, find real-world usage patterns. Researcher spins up a subagent per avenue, runs them in parallel, and synthesizes. This is where decomposition earns its keep — three focused searches converge faster than one agent doing them serially.

**Seeded with:**
- `research-approach.md` — How to research well. Start with the question, not the tool. Evaluate sources for recency and authority. Compare at least two approaches before recommending one. Always surface trade-offs, not just winners.
- `source-evaluation.md` — How to judge whether information is reliable. Official docs > blog posts > StackOverflow > LLM training data. Recent > old. Maintained > abandoned.
- `recommendation-format.md` — How to deliver findings. Not a research paper — a decision-ready brief: "Here's the question. Here are the options. Here's what I recommend and why. Here's what you'd lose by choosing differently."
- `decomposition.md` — When and how to spawn subagents for parallel research. (This skill is shared — see below.)

**Heartbeat:** On-demand primarily (called by other agents). But also daily: scan `learnings/failures/` for patterns that suggest missing knowledge. If Builder keeps failing at the same category of problem, proactively research it.

### 2. Spec (The Architect)

**What it does:** Takes a fuzzy intent ("I need a CLI tool that syncs Notion to local Markdown") and produces an NLSpec — a natural language specification detailed enough that the other agents can implement it without asking clarifying questions. Leans heavily on Researcher when a domain is unfamiliar.

**Why it exists:** StrongDM's deepest lesson is that the quality of agent-produced software is bounded by the quality of the specification. Their 6,000-line NLSpecs aren't bureaucracy — they're the *actual product*. The code is a derivative. Spec is the agent that does the hardest human-adjacent work: understanding what you actually want, asking the right questions, and writing it down precisely.

**How it uses Researcher:** Before writing a spec for anything non-trivial, Spec writes a research request to `tasks/research/`: "I need to spec a system that does X. What are the established approaches? What are the key design decisions?" Researcher investigates and drops a brief into `tasks/research-done/`. Spec reads it and incorporates the findings into the NLSpec — not as implementation instructions, but as informed constraints: "This system should use approach Y because Z."

**Seeded with:**
- `spec-writing.md` — How to write NLSpecs. Structure, level of detail, what to make explicit vs. what to leave to the implementer. Draws from Attractor's pattern: behavioral constraints, interface semantics, system boundaries.
- `domain-interview.md` — How to interview the human. What questions to ask. When to push for more detail vs. when to say "that's enough, I can spec this."
- `spec-patterns/` — A growing library of spec templates: CLI tools, web APIs, data pipelines, libraries, full-stack apps. Each one is a skeleton NLSpec for that type of project.
- `project-memory.md` — Running context on all active projects. What exists, what state it's in, what the human cares about.

**Heartbeat:** Every morning. Checks: are there projects in progress with stale specs? Has the human mentioned anything that needs speccing? Any Builder failures that suggest the spec was underspecified?

### 3. Builder (The Implementer)

**What it does:** Takes a spec and produces working code. This is the Attractor-style non-interactive coding agent — it receives a fully-specified task and runs to convergence without asking questions.

**Why it exists separately from Spec:** Separation of concerns, but also separation of *models*. Builder benefits from deep coding ability and long context for holding entire codebases. Spec benefits from reasoning, ambiguity tolerance, and the ability to ask good questions. Different cognitive profiles. You might run Builder on a model optimized for code and Spec on one optimized for reasoning.

**Seeded with:**
- `implementation-patterns.md` — How to go from spec to code. File structure conventions. When to scaffold first vs. write linearly. How to handle ambiguity in a spec (write the conservative interpretation, flag the ambiguity in a note).
- `language-stacks/` — Per-language/framework skills: `python-project.md`, `typescript-node.md`, `rust-cli.md`, `react-app.md`. Not tutorials — conventions. "In this stack, here's how we structure projects, handle errors, write tests, manage dependencies."
- `tool-use.md` — How to use the filesystem, shell, git. Builder's tool vocabulary.
- `convergence.md` — How to know when you're done. Run tests. Check the spec. If tests pass and spec is satisfied, stop. If not, iterate — but if you've iterated 3 times on the same issue, write a failure note and stop.

**Heartbeat:** Continuous when working. Checks `tasks/building/` for assigned specs. When idle, checks for maintenance tasks (dependency updates, failing CI, open issues).

### 4. Verifier (The Judge)

**What it does:** Evaluates whether Builder's output actually satisfies the spec. Runs tests. Reads code. Compares against scenario holdouts. Produces a satisfaction assessment.

**Why it exists separately from Builder:** This is the StrongDM trust model. The agent that produces work must not be the agent that evaluates it. Verifier has access to things Builder doesn't — the scenario holdouts stored in `scenarios/` — and explicitly does NOT have access to Builder's work-in-progress reasoning or intermediate attempts. It sees only the final artifact.

**Seeded with:**
- `verification-approach.md` — How to verify. Not just "run the tests." Read the spec. Read the code. Do they match? Are there edge cases the spec mentions that the tests don't cover? Are there behaviors the code exhibits that the spec doesn't describe?
- `satisfaction-scoring.md` — The probabilistic satisfaction metric. Not pass/fail. A judgment: "Of a population of users who wanted what the spec describes, what fraction would be satisfied with this output?" With reasoning.
- `scenario-evaluation.md` — How to evaluate against holdout scenarios. Run the scenario mentally or actually. Does the system behave as the scenario expects?
- `failure-reporting.md` — How to write a useful failure report. Not "it's wrong." What's wrong, why it matters, what the spec says, what the code does, and a suggested path to fix.

**Heartbeat:** Triggers whenever Builder marks a task as done. Also periodic: re-verify existing projects against their scenarios (regression checking).

**Critical constraint:** Verifier cannot read `tasks/building/` (Builder's work-in-progress). It can only read `tasks/review/` (completed work submitted for verification). Verifier cannot edit specs or code — it can only write assessments and failure reports.

### 5. Librarian (The Memory)

**What it does:** Manages the collective knowledge of the system. Curates shared memory. Reviews self-authored skills. Detects patterns across projects. Maintains the `learnings/` directory. Compresses and indexes.

**Why it exists:** OpenClaw's self-improvement loop is powerful but dangerous without curation. An agent that writes skills in the heat of a debugging session might write something too specific, too wrong, or redundant with an existing skill. Librarian is the steady hand that reviews, edits, organizes, and occasionally prunes.

**Seeded with:**
- `knowledge-curation.md` — How to review a proposed skill. Is it general enough? Is it accurate? Does it conflict with existing skills? Is it well-written enough for another agent to use?
- `pattern-detection.md` — How to spot recurring patterns across projects. If Builder hits the same snag in three different Rust projects, that's a pattern. Write a skill for it.
- `memory-hygiene.md` — How to keep memory clean. Archive stale daily logs. Promote important findings from daily logs to long-term memory. Remove contradictions.
- `indexing.md` — How to maintain the semantic search index. What to index, how to chunk, when to re-index.

**Heartbeat:** Daily. Reviews everything that happened in the last 24 hours: new learnings, proposed skills, Builder failures, Verifier assessments. Promotes, merges, prunes, organizes.

### 6. Operator (The Runner)

**What it does:** Handles the non-creative operational work: git operations, CI/CD, dependency management, deployment, monitoring. The agent that keeps the lights on across all projects.

**Why it exists:** Builder should be thinking about implementation, not about whether the CI pipeline is configured correctly or whether there's a new security advisory for a dependency. Operator handles the infrastructure and maintenance that every project needs but that distracts from the core work.

**Seeded with:**
- `git-workflow.md` — Branching strategy, commit conventions, PR management. How to handle merge conflicts.
- `ci-cd.md` — How to set up and maintain CI/CD per stack. GitHub Actions patterns, testing configurations, deployment scripts.
- `dependency-management.md` — How to audit, update, and manage dependencies. When to update vs. when to pin. How to evaluate whether an update is safe.
- `monitoring.md` — How to check if deployed projects are healthy. What "healthy" means per project type.
- `project-registry.md` — The master list of all projects, their repos, their CI status, their deployment targets.

**Heartbeat:** Hourly. Checks CI status across all projects. Checks for dependency advisories. Checks for stale branches. Reports anything that needs attention.

---

## The Workspace

```
factory/
│
├── agents.yaml                    # Agent definitions (model, skills, memory scope, heartbeat)
│
├── specs/
│   ├── inbox/                     # Raw intents from the human ("I need a thing that...")
│   ├── drafting/                  # Spec is working on these
│   ├── ready/                     # Specced and ready for Builder
│   └── archive/                   # Completed specs (reference library)
│
├── tasks/
│   ├── research/                  # Research requests from any agent
│   ├── research-done/             # Completed research briefs
│   ├── building/                  # Builder's work-in-progress (Verifier CANNOT see this)
│   ├── review/                    # Completed work awaiting verification
│   ├── verified/                  # Passed verification
│   ├── failed/                    # Failed verification (with failure reports)
│   └── maintenance/               # Ongoing maintenance tasks (Operator's domain)
│
├── scenarios/                     # HOLDOUT — working agents cannot read this directory
│   ├── {project-name}/            # Per-project scenario sets
│   │   ├── scenario-001.md        # End-to-end user story
│   │   ├── scenario-002.md
│   │   └── satisfaction.md        # Latest satisfaction assessment
│   └── meta/                      # Scenarios for the factory itself
│
├── skills/
│   ├── shared/                    # Approved skills available to all agents
│   ├── proposed/                  # Self-authored skills awaiting Librarian review
│   ├── researcher/                # Researcher-specific skills
│   ├── spec/                      # Spec-specific skills
│   ├── builder/                   # Builder-specific skills
│   ├── verifier/                  # Verifier-specific skills
│   ├── librarian/                 # Librarian-specific skills
│   └── operator/                  # Operator-specific skills
│
├── memory/
│   ├── shared/                    # Cross-agent knowledge (curated by Librarian)
│   │   ├── KNOWLEDGE.md           # Durable facts, decisions, conventions
│   │   └── PROJECTS.md            # Master project status document
│   ├── daily/                     # Append-only daily logs per agent
│   │   ├── researcher/
│   │   ├── spec/
│   │   ├── builder/
│   │   ├── verifier/
│   │   ├── librarian/
│   │   └── operator/
│   └── {agent}/                   # Private curated memory per agent
│       └── MEMORY.md
│
├── learnings/
│   ├── failures/                  # What went wrong and why
│   │   └── {date}-{project}-{summary}.md
│   ├── corrections/               # Human corrections (highest signal)
│   │   └── {date}-{summary}.md
│   └── discoveries/               # New patterns, better approaches
│       └── {date}-{summary}.md
│
├── universe/                      # The factory's reference universe — its DTU equivalent
│   ├── README.md                  # What this is and how agents should use it
│   ├── attractor/                 # StrongDM's Attractor specs (verbatim)
│   │   ├── attractor-spec.md
│   │   ├── coding-agent-loop-spec.md
│   │   └── unified-llm-spec.md
│   ├── context-engineering/       # Koylan's key skills (verbatim)
│   │   ├── context-fundamentals.md
│   │   ├── context-degradation.md
│   │   ├── multi-agent-patterns.md
│   │   └── memory-systems.md
│   ├── synthesis/                 # Our own thinking
│   │   ├── how-the-butterflies-flutter.md
│   │   └── factory-blueprint.md   # This document
│   └── willison/                  # Key insights from the Software Factory analysis
│       └── software-factory-principles.md
│
├── projects/                      # The actual codebases
│   ├── {project-name}/            # Each project is a git repo
│   │   ├── .factory/              # Factory metadata for this project
│   │   │   ├── spec.md            # The NLSpec that generated this project
│   │   │   ├── history.md         # What's been done, by whom, when
│   │   │   └── notes.md           # Agent notes about this project
│   │   └── ...                    # The actual source code
│   └── ...
│
└── runs/                          # Execution history (Attractor-style)
    └── {run-id}/
        ├── graph.dot              # Pipeline definition (if using graph orchestration)
        ├── checkpoint.json
        └── nodes/
```

### Access Control (Filesystem-Level Trust)

This is where the "who watches the watchers" principle becomes concrete:

| Agent | Can Read | Can Write | Cannot Access |
|-------|----------|-----------|---------------|
| Researcher | `tasks/research/`, `memory/shared/`, own memory, `skills/shared/`, `skills/researcher/`, `learnings/`, `projects/` (read-only) | `tasks/research-done/`, own memory, `skills/proposed/`, own daily log | `scenarios/`, `tasks/building/` |
| Spec | `specs/`, `tasks/research-done/`, `memory/shared/`, own memory, `skills/shared/`, `skills/spec/`, `learnings/` | `specs/drafting/`, `specs/ready/`, `tasks/research/`, own memory, `skills/proposed/`, own daily log | `scenarios/`, `tasks/building/` |
| Builder | `specs/ready/`, `tasks/research-done/`, `skills/shared/`, `skills/builder/`, own memory, `projects/`, `learnings/` | `tasks/building/`, `tasks/review/`, `tasks/research/`, `projects/`, own memory, `skills/proposed/`, own daily log | `scenarios/`, `tasks/review/` (after handoff) |
| Verifier | `specs/ready/`, `tasks/review/`, `scenarios/`, `skills/shared/`, `skills/verifier/`, own memory, `projects/` | `tasks/verified/`, `tasks/failed/`, `tasks/research/`, `scenarios/*/satisfaction.md`, own memory, `skills/proposed/`, own daily log | `tasks/building/` |
| Librarian | Everything in `skills/`, `memory/`, `learnings/`, daily logs | `skills/shared/` (promote), `skills/proposed/` (edit), `memory/shared/`, `learnings/` | `scenarios/`, `tasks/building/` |
| Operator | `projects/`, `tasks/maintenance/`, `skills/shared/`, `skills/operator/`, `memory/shared/`, own memory | `projects/`, `tasks/maintenance/`, own memory, `skills/proposed/`, own daily log | `scenarios/`, `tasks/building/`, `specs/drafting/` |

Note: **any agent can write to `tasks/research/`** to request Researcher's help. This is the one cross-agent communication channel that doesn't go through the filesystem state-machine — it's a direct request for expertise.

The key asymmetry: **Verifier can see scenarios, Builder cannot.** This is the holdout principle from StrongDM. It prevents Builder from overfitting to the verification criteria.

### The Universe (`universe/`)

This is the factory's equivalent of StrongDM's Digital Twin Universe — except instead of cloning Okta and Jira, we're cloning the *ideas the factory is built on*. The universe directory contains the verbatim source documents that informed the factory's design: Attractor's three specs, Koylan's context engineering skills, the Willison analysis, and our own synthesis docs.

**Any agent can read `universe/`.** It's the reference SDK for the factory's own philosophy. When Librarian reviews a proposed skill, it can check whether the skill aligns with the context engineering principles. When Researcher is investigating an approach, it can check whether Attractor already solved that problem. When Builder is implementing the factory's own infrastructure, it can read the spec it's supposed to be building from.

The universe is **read-only for all agents** — it's reference material, not working state. Only the human updates it (by adding new source documents or updating the synthesis). This prevents agents from editing their own philosophical foundations, which would be the deepest form of the "who watches the watchers" problem.

---

## Seed Skills in Detail

### The Minimum Seed Set (What You Write Before Anything Runs)

These are the skills that bootstrap the system. They need to be written by a human (you) because the agents don't exist yet to write them. Everything after this can be self-authored.

**For all agents — `skills/shared/`:**

```markdown
# self-improvement.md
---
name: self-improvement
description: When you encounter a failure, correction, or new pattern, write a learning and optionally propose a new skill.
---

## When to activate
- A tool call fails unexpectedly
- The human corrects you
- You discover a better approach to something you've done before
- You notice a pattern across multiple tasks

## What to do
1. Write a learning to `learnings/failures/`, `learnings/corrections/`, or `learnings/discoveries/`
   - Format: `{YYYY-MM-DD}-{project-or-context}-{brief-summary}.md`
   - Include: what happened, what you expected, what you learned, what should change
2. If the learning suggests a reusable skill:
   - Write a SKILL.md to `skills/proposed/{skill-name}/SKILL.md`
   - Librarian will review it on next heartbeat
3. Update your daily log with a brief note about the learning

## What NOT to do
- Don't modify skills in `skills/shared/` directly — always propose
- Don't write a skill for something that happened once (wait for patterns)
- Don't write learnings that are just "this didn't work" without analysis
```

```markdown
# filesystem-conventions.md
---
name: filesystem-conventions
description: How the factory workspace is organized and what each directory means.
---

## Directory purposes
[the workspace structure from above, annotated with what each agent should and shouldn't touch]

## File naming
- Learnings: `{YYYY-MM-DD}-{project}-{summary}.md`
- Daily logs: `memory/daily/{agent}/{YYYY-MM-DD}.md`
- Tasks: named by spec they implement, with status indicated by which directory they're in
- Skills: `skills/{scope}/{skill-name}/SKILL.md`

## The cardinal rules
- The filesystem IS the coordination protocol. Don't try to "message" other agents.
  Write files where other agents will find them.
- Moving a file between directories IS a state transition.
  `tasks/building/foo` → `tasks/review/foo` means "I'm done, verify this."
- Git tracks everything. Commit after every meaningful state change.
```

```markdown
# decomposition.md
---
name: decomposition
description: When and how to spawn subagents for parallel work. Any root agent can decompose.
---

## When to decompose
- A task has 3+ independent facets that could be explored in parallel
- You're about to do the same thing serially for multiple items (research 3 libraries, verify 4 modules, build 3 independent components)
- The task would push your context past the yellow zone (>30% of window) if done in a single session
- You need to try multiple approaches and pick the best one

## When NOT to decompose
- The task is sequential (step 2 depends on step 1's output)
- The overhead of coordinating subagents exceeds the work itself
- The task fits comfortably in your context window as a single effort
- You're already a subagent (no recursive decomposition — keep the tree shallow)

## How to decompose
1. Write a decomposition plan to your daily log: what subagents, what each one does, what you expect back
2. For each subagent, write a scoped task file to `tasks/{your-name}-sub/`:
   - Clear objective (one paragraph)
   - What to read (specific files/directories)
   - What to produce (specific output file)
   - Constraints (context budget, time limit, scope boundary)
3. Spawn subagents (execution layer handles this)
4. When subagents complete, read their outputs
5. Synthesize into your own output — don't just concatenate
6. Subagent task files and outputs are ephemeral — Librarian may harvest learnings but the rest is cleaned up

## Subagent constraints
- Subagents inherit your skills but NOT your memory (they start clean)
- Subagents cannot spawn their own subagents (max depth = 1)
- Subagents cannot write to `skills/proposed/` — only root agents can propose skills
- Subagents write to `tasks/{parent-agent}-sub/{sub-id}/output.md` and nowhere else
- Subagent context budget: hard cap at green zone (≤30% of window)
```

```markdown
# context-discipline.md
---
name: context-discipline
description: How to manage your context window. Load only what you need. Write to disk before you forget.
---

## Before starting any task
1. Read only the specific spec/task you're working on
2. Load only the skills relevant to this task
3. Read your private MEMORY.md for relevant prior context
4. Read shared KNOWLEDGE.md only if the task involves cross-project concerns

## During long tasks
- If you've been working for many turns, pause and write a checkpoint:
  your current understanding, what you've done, what's left
- Write it to your daily log, not just to memory
- This protects you from context compaction losing important state

## When finishing a task
- Write a summary to your daily log
- If you learned anything durable, write to learnings/
- Don't carry context from one task to the next — start fresh
```

**For Researcher — `skills/researcher/`:**

```markdown
# research-approach.md
---
name: research-approach
description: How to research a question and deliver a decision-ready recommendation.
---

## The sequence
1. Clarify the question. What exactly does the requesting agent need to know?
   Not "research React" — "which React state management approach best fits a
   real-time collaborative app with optimistic updates?"
2. Identify 2-4 candidate approaches. Never research just one option.
3. For each candidate:
   - Find authoritative sources (official docs, reputable technical writing, maintained repos)
   - Evaluate: maturity, maintenance status, community size, known pitfalls
   - Note trade-offs honestly — there's rarely a clear winner
4. Synthesize into a recommendation brief:
   - The question (restated precisely)
   - The candidates (1-2 paragraphs each)
   - The recommendation (which one and why)
   - The trade-off (what you lose by choosing the recommendation)
   - Confidence level (high/medium/low with reasoning)
5. Write the brief to `tasks/research-done/{request-id}.md`

## When to decompose
Research is the most natural place for subagents. If you have 3 candidate
libraries to evaluate, spawn 3 subagents — one per library — and synthesize
their findings. Each subagent reads docs, checks maintenance status, finds
usage examples. You compare and recommend.

## Source hierarchy
1. Official documentation (current version)
2. Source code and tests (the actual behavior)
3. Maintained technical blogs by practitioners
4. Conference talks and technical papers
5. Community forums (useful for gotchas, not for architecture)
6. Your own training knowledge (lowest confidence — flag as such)

## What a good brief looks like
Short. Decision-ready. The requesting agent should be able to read it in 2 minutes
and know what to do. If your brief is longer than 500 words, you're writing a report
instead of a recommendation. Save the details for a linked appendix.
```

**For Spec — `skills/spec/`:**

```markdown
# nlspec-format.md
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
Be explicit about edge cases — these are where Builder most often underspecifies.

### 5. Out of Scope
Explicitly state what this spec does NOT cover. This prevents Builder from gold-plating.

### 6. Verification Criteria
How Verifier should know this works. Not test cases (those are holdouts),
but observable properties: "A user should be able to [action] and see [result]."

## The quality test
A spec is ready when you can hand it to a competent developer who has
never heard of this project and they can build it without asking a single question.
If they'd need to ask something, the spec is missing that information.
```

**For Builder — `skills/builder/`:**

```markdown
# implementation-approach.md
---
name: implementation-approach
description: How to go from spec to working code.
---

## The sequence
1. Read the full spec. Don't start coding until you understand the whole thing.
2. Scaffold the project structure first: directories, config files, dependency manifest, empty test file.
3. Implement the core behavior — the thing that makes this project *this project* and not some other project.
4. Implement the interfaces (CLI, API, file I/O) that expose the core behavior.
5. Write tests that exercise the verification criteria from the spec.
6. Run the tests. Fix what's broken. Repeat until green.
7. Read the spec one more time. Check every behavioral requirement against your implementation.
8. Write a brief summary of what you built and any deviations from the spec to `tasks/review/{task}/builder-notes.md`.
9. Move the task from `tasks/building/` to `tasks/review/`.

## When you're stuck
- If the spec is ambiguous: implement the most conservative interpretation and note the ambiguity.
- If you've tried 3 different approaches to the same problem: write a failure learning and stop. Don't thrash.
- If a dependency doesn't work as expected: note it, find an alternative, and propose a skill about the issue.

## What "done" means
- All tests pass
- All behavioral requirements from the spec are implemented
- The project can be cloned and run by someone who has never seen it
- builder-notes.md exists and is honest about any deviations or concerns
```

**For Verifier — `skills/verifier/`:**

```markdown
# verification-protocol.md
---
name: verification-protocol
description: How to evaluate whether Builder's output satisfies the spec.
---

## The sequence
1. Read the spec in `specs/ready/`.
2. Read Builder's notes in `tasks/review/{task}/builder-notes.md`.
3. Clone/read the project in `projects/{project}/`.
4. Run the existing tests. Note results.
5. Read the scenario holdouts in `scenarios/{project}/`.
6. For each scenario: walk through it against the actual code/system. Does it work as the scenario describes?
7. Score satisfaction: "Of 10 users who wanted what the spec describes, how many would be satisfied with this?"
8. Write your assessment:
   - If satisfied (≥8/10): move to `tasks/verified/`, write assessment to `scenarios/{project}/satisfaction.md`
   - If not satisfied: move to `tasks/failed/`, write a failure report explaining exactly what's wrong
     and what the spec requires. Builder will use this to iterate.

## What you're checking
- Behavioral correctness: does the system DO what the spec says?
- Boundary correctness: does the system handle edges, errors, and constraints as specified?
- Completeness: is anything in the spec NOT implemented?
- Excess: is anything implemented that's NOT in the spec? (This is also a failure — gold-plating wastes time.)

## What you are NOT checking
- Code style (unless the spec mentions it)
- Performance (unless the spec has performance constraints)
- Whether you'd have implemented it differently
```

---

## The Bootstrap Sequence

This is the order in which you bring the system to life. Each step should work before moving to the next.

### Step 0: Create the workspace

```bash
mkdir -p factory/{specs/{inbox,drafting,ready,archive},tasks/{research,research-done,building,review,verified,failed,maintenance},scenarios/meta,skills/{shared,proposed,researcher,spec,builder,verifier,librarian,operator},memory/{shared,daily/{researcher,spec,builder,verifier,librarian,operator},researcher,spec,builder,verifier,librarian,operator},learnings/{failures,corrections,discoveries},projects,runs}

cd factory && git init
```

Write the seed skills above into their respective directories. Commit.

### Step 1: Researcher + Spec + Builder (the minimum triangle)

Start with three agents, not two. The reason: your first project will involve a domain decision. Researcher investigates the options. Spec writes the NLSpec informed by Researcher's brief. Builder implements it.

Your first intent: something small and real. Not "build a factory." Something like "build a CLI tool that watches a directory for new Markdown files and indexes them for full-text search." Small enough to finish in one session. Real enough to exercise the full research→spec→build loop. And the research question is real too: what's the best full-text search approach for a local CLI tool? Researcher evaluates sqlite FTS5 vs. tantivy vs. ripgrep-style regex, recommends one, Spec writes the NLSpec, Builder builds it.

**What you're testing:** Does the triangle work? Does Researcher's brief actually improve the spec? Does Spec write a spec good enough for Builder to implement? Where does Builder get confused? Those confusions are your first learnings — and your first self-authored skills.

### Step 2: Add Verifier (the trust loop)

Write 2-3 scenario holdouts for the project from Step 1. Put them in `scenarios/`. Let Verifier evaluate Builder's output.

**What you're testing:** Does Verifier catch things Builder missed? Does the feedback loop (Verifier fails → Builder retries) converge? How many rounds does it take? Does Verifier request research from Researcher to calibrate its judgment?

### Step 3: Add Librarian (the learning loop)

By now you have some learnings in `learnings/`, some proposed skills in `skills/proposed/`, and some daily logs. Librarian's job is to make sense of this.

**What you're testing:** Does Librarian produce useful curation? Do the promoted skills actually help on the next project?

### Step 4: Add Operator + Heartbeat (the living system)

Operator starts managing git, CI, dependencies across projects. Heartbeats start running on cron.

**What you're testing:** Does the system feel alive? Do agents surface useful things proactively? Or does the heartbeat produce noise?

### Step 5: Test decomposition

Give the factory a project big enough that at least one agent needs to decompose. Something with 3-4 independent modules, or a research question with multiple competing approaches. Watch whether subagent spawning, parallel execution, and synthesis actually work — or whether they add overhead without payoff.

**What you're testing:** Is decomposition a natural capability or a forced abstraction? Where does it help and where does it hurt?

### Step 6: Feed it itself

The factory's first real test: use it to improve itself. Write a spec for a feature of the factory. Maybe "add graph-based pipeline orchestration for multi-step tasks" (bringing in Attractor's DOT-based model). Let the factory build it. Researcher investigates Attractor's patterns. Spec writes an NLSpec for the orchestrator. Builder implements it. Verifier evaluates it against the meta-scenario.

**What you're testing:** Whether the system can reason about its own architecture and extend itself. This is where it either becomes self-sustaining or hits a wall.

---

## What Model Where

| Agent | Recommended Model | Why |
|-------|------------------|-----|
| Researcher | Claude Opus / o3 | Needs strong reasoning + synthesis across diverse sources. Worth the cost — bad research poisons everything downstream. |
| Spec | Claude Opus / o3 | Needs the strongest reasoning for ambiguity resolution and question-asking |
| Builder | Claude Sonnet / Codex | Needs fast, reliable code generation with good tool use |
| Verifier | Claude Opus / o3 | Needs judgment, not speed. Satisfaction scoring is a reasoning task. |
| Librarian | Claude Sonnet / Haiku | Pattern detection and curation don't need the biggest model |
| Operator | Claude Haiku / GPT-4o-mini | Routine operations. Fast and cheap. |
| Subagents | Claude Haiku / GPT-4o-mini | Scoped, ephemeral, constrained to green zone. Speed and cost matter more than depth. |

The key insight from Attractor: the pipeline definition doesn't change when you swap models. You can start with Sonnet everywhere and upgrade individual agents as you find where reasoning quality matters most.

---

## The Meta-Scenario

Write this into `scenarios/meta/factory-itself.md` on day one:

*A solo developer with a new project idea should be able to describe it in 2-3 sentences, leave, and come back to find: a complete NLSpec they can review, a working implementation, a verification assessment, and a list of what the system learned from building it. The developer's only job is to approve the spec and approve the final result. Everything in between is the factory's problem.*

That's the satisfaction criterion for the factory itself. When it can do that reliably, it's working.

---

## Sources

- [StrongDM Attractor Spec](https://github.com/strongdm/attractor/blob/main/attractor-spec.md) — Graph-based pipeline orchestration, goal gates, convergence
- [StrongDM Coding Agent Loop](https://github.com/strongdm/attractor/blob/main/coding-agent-loop-spec.md) — Inner loop design, provider alignment, loop detection
- [Simon Willison on the Software Factory](https://simonwillison.net/2026/Feb/7/software-factory/) — Scenario holdouts, satisfaction metrics, digital twins
- [OpenClaw Architecture](https://ppaolo.substack.com/p/openclaw-system-architecture-overview) — Skills as Markdown, file-based memory, heartbeat
- [OpenClaw Self-Improving Agent](https://playbooks.com/skills/openclaw/skills/self-improving-agent) — Self-authoring loop
- [Agent Skills for Context Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) — Progressive disclosure, attention budgeting, multi-agent patterns
