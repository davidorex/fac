# How the Butterflies Flutter Together

## Four projects. One emerging shape.

This isn't a feature comparison. It's an attempt to watch four different groups of people solve the same problem from different angles and notice where their solutions converge — not in their specifics, but in their *instincts*. The projects:

- **OpenClaw** — a personal AI agent runtime that went from a WhatsApp relay script to 175k GitHub stars in two weeks
- **Agent Skills for Context Engineering** (Murat Can Koylan) — a theoretical framework for managing what goes into an agent's attention window
- **Attractor** (StrongDM) — a non-interactive coding agent specified entirely in natural language, designed for a "Software Factory"
- **Simon Willison's "Software Factory" write-up** — the sharpest outside analysis of what StrongDM is actually doing and what it means

Each of these is doing something genuinely different. But they're all responding to the same wind.

---

## The Wind

Here's the thing none of these projects says outright, but all of them embody: **the agent loop is solved. The interesting problems are now environmental.**

OpenClaw's creator Peter Steinberger understood this from the start — the hard problem isn't getting an LLM to reason and call tools in a cycle. That's a while loop with an API call. The hard problem is everything *around* the loop: What context does the agent see? How does it remember? How does it learn? How do you trust it? How do multiple agents coordinate without drowning in their own coordination overhead?

StrongDM arrived at the same place from a completely different direction. Their Attractor spec is a graph-based pipeline orchestrator — but it deliberately has *no opinion* about the agent loop inside each node. You can plug in Claude Code, Codex, Gemini CLI, a raw API call, whatever. The loop is a commodity. The graph of *how loops relate to each other* — that's the design surface.

And Koylan's Context Engineering framework makes the theoretical case: models degrade predictably as context grows. The "lost-in-the-middle" phenomenon, U-shaped attention curves, attention scarcity. The ceiling on agent capability isn't the model's intelligence. It's the quality of what reaches the model's attention. Context engineering — the discipline of curating the smallest possible set of high-signal tokens — is where leverage lives.

So: the loop is solved, context is the bottleneck, and the environment is the design surface. That's the wind.

---

## Three Deep Patterns

### Pattern 1: Specifications as the Unit of Work (Not Code)

This is the most radical convergence. All four projects, in different ways, are moving toward a world where **humans write specifications and agents write implementations**.

StrongDM makes this explicit with two principles Willison highlighted: "Code must not be written by humans" and "Code must not be reviewed by humans." Their three-person team operates by writing NLSpecs — natural language specifications so detailed that a coding agent can implement them without clarification. The Attractor repo itself is the proof: it contains zero code. Just three markdown files totaling roughly 6,000-7,000 lines of specification. You hand it to a coding agent and say "implement this."

OpenClaw's skill system does the same thing at a different granularity. A SKILL.md file isn't code — it's a specification for behavior. When an agent loads a skill, it's receiving instructions, not executing a program. The skill says "when the user asks for X, here's how to think about it, here's what tools to use, here's what good output looks like." The agent implements that specification fresh each time.

Koylan's framework names the deeper principle: **progressive disclosure**. On startup, the agent sees only skill names and ~97-character descriptions. Full specifications load only when needed. This isn't just an optimization — it's a statement about what agents should be doing with their attention. Not holding code in memory. Holding specifications, and generating behavior from them.

What this means for a local framework: **the workspace is a library of specifications, not a codebase.** Tasks are specs. Skills are specs. Agent definitions are specs. Memory is narrative, not structured data. Everything the agents touch is human-readable, human-auditable natural language that describes intent.

### Pattern 2: Convergence Through Verification, Not Control

Here's where Willison's analysis cuts deepest. The obvious question about a software factory is: if no human writes or reviews the code, how do you trust it?

StrongDM's answer isn't more control. It's more verification, structured differently. Three ideas layer together:

**Scenarios as holdout sets.** Inspired by Cem Kaner's scenario testing, StrongDM stores end-to-end user stories *outside the codebase* — deliberately hidden from the coding agents, the way you'd withhold test data from a model being trained. This prevents reward hacking: the agent can't optimize for passing the tests because it can't see the tests.

**Satisfaction, not correctness.** They moved from boolean pass/fail to a probabilistic metric: of all observed trajectories through all scenarios, what fraction likely satisfies the user? This is a profound shift. Traditional testing asks "does this work?" StrongDM asks "would a human be satisfied?" — and uses LLM-as-judge to evaluate.

**The Digital Twin Universe.** Behavioral clones of third-party services (Okta, Jira, Slack, Google Workspace) that let agents test at volumes and speeds impossible against live services. This is environment-building in service of verification — you don't trust the agent more, you build a world where trust can be measured empirically.

OpenClaw's self-improvement loop has the same shape, though less formally. The agent observes a failure, writes a learning, authors a new skill, and that skill persists. The "verification" is implicit: if the skill works next time, it stays. If it doesn't, it gets revised. This is convergence through iteration, not convergence through human review.

Attractor formalizes this as **goal gates with retry logic**. Nodes in the execution graph can be marked as goal gates — they must reach SUCCESS before the pipeline can exit. If they don't, the system routes to a retry target and re-executes. Convergence is structural: the graph *won't let you leave* until quality conditions are met. The exit node checks all gates. Unsatisfied gates trigger re-traversal. The system loops until it converges or exhausts retries.

The pattern across all three: **don't try to make agents correct on the first try. Build environments where they converge on correctness through structured iteration.** Design for convergence, not perfection. Make failure cheap, verification continuous, and iteration automatic.

### Pattern 3: The Filesystem as Shared Mind

This is the pattern that's easiest to miss because it's so simple it doesn't feel like architecture.

OpenClaw stores everything in Markdown files on disk. Memory, skills, configuration — all plain text, all greppable, all version-controllable. No database. The Markdown files *are* the source of truth; search and indexing sit on top as acceleration layers, not as the canonical store.

Attractor stores execution state as checkpoints in a file tree:
```
runs/{run_id}/
├── checkpoint.json
├── nodes/{node_id}/
│   ├── outcome.json
│   ├── output.txt
│   └── artifacts/
```

Every node's inputs and outputs are files. The run directory is a complete, resumable record of everything that happened. You can inspect it, replay from any checkpoint, debug by reading files.

StrongDM's CXDB — their "AI Context Store" — persists conversation histories and tool outputs in an immutable DAG. It's more structured than OpenClaw's flat Markdown, but the instinct is the same: the record of what agents have done and thought needs to be durable, inspectable, and separate from the agent's runtime.

Koylan's framework calls this **filesystem-as-context**: the directory structure itself encodes relationships. Agents discover what they need by reading the filesystem rather than having it pre-loaded into their prompt. Dynamic discovery over static injection.

For a multi-agent local framework, this pattern becomes the coordination mechanism itself. Agents don't send messages to each other. They write files. The filesystem is the shared mind:

- An agent picks up a task by moving a file from `tasks/inbox/` to `tasks/in-progress/`
- It writes its work product to `tasks/{id}/artifacts/`
- It records what it learned in `learnings/`
- Another agent discovers that learning by reading the filesystem on its next turn
- Shared memory is a set of Markdown files that any agent can read and append to

No message queues. No RPC. No coordination protocols. Just files, and agents that know how to read them.

---

## What Emerges When They Flutter Together

If you let these four projects inform each other rather than compete, a shape emerges for what a locally-run multi-agent framework actually wants to be:

### The Workspace Is the System

There's no "server" to run. There's a directory on your machine with a specific structure. The workspace *is* the multi-agent system. Everything — skills, memory, tasks, agent definitions, execution history, learnings — lives as files in this directory. Git is your database. The filesystem is your message queue. Markdown is your programming language.

```
factory/
├── specs/                    # Natural language specifications (the "what")
│   ├── active/               # Specs currently being worked
│   └── archive/              # Completed specs
│
├── scenarios/                # Verification holdouts (hidden from working agents)
│   ├── satisfaction/         # LLM-judged scenario evaluations
│   └── twins/                # Digital twin configs for external services
│
├── skills/                   # Behavioral specifications for agents
│   ├── shared/               # Available to all agents
│   ├── proposed/             # Self-authored, awaiting review
│   └── {agent-name}/         # Agent-specific skills
│
├── memory/
│   ├── shared/               # Cross-agent knowledge
│   ├── daily/                # Append-only daily logs per agent
│   └── {agent-name}/         # Private curated memory
│
├── runs/                     # Execution history (Attractor-style)
│   └── {run-id}/
│       ├── graph.dot         # The pipeline that was executed
│       ├── checkpoint.json   # Resumable state
│       └── nodes/            # Per-node outcomes and artifacts
│
├── learnings/                # Self-improvement artifacts
│   ├── corrections/
│   ├── failures/
│   └── discoveries/
│
└── agents.yaml               # Who the agents are and what they can do
```

### Agents Are Defined by What They Read, Not What They Run

Each agent is a model + a set of skills + a memory scope + a heartbeat schedule. That's it. The "code" each agent runs is the same: the agentic loop (assemble context → invoke model → execute tools → persist state). What differentiates them is what context they assemble — which skills they load, which memory they read, which part of the filesystem they watch.

This is Attractor's CodergenBackend principle applied universally: the pipeline definition (the graph, the specs, the skills) is completely independent of the execution backend. Swap Claude for GPT for Gemini for a local model — the workspace doesn't change.

### Work Flows as Graphs, Not Messages

Attractor's deepest contribution is making the workflow a *graph you can see*. DOT syntax, Graphviz-renderable, version-controllable. Nodes are tasks. Edges are transitions with conditions. Goal gates ensure quality. Retry logic handles failure.

For a local team, this means complex multi-step work isn't coordinated by agents chatting with each other. It's coordinated by a graph that defines the pipeline — who does what, in what order, under what conditions. The graph is a Markdown file (or DOT file) in the workspace. Agents traverse it. Humans can read it, edit it, and understand what's happening at a glance.

The heartbeat pattern from OpenClaw fits here too. The graph isn't traversed in one shot. Agents wake up periodically, check where they are in the graph, do the next piece of work, and go back to sleep. The cron job *is* the execution engine.

### Trust Comes from the Environment, Not the Agent

This is the thread that ties StrongDM's "satisfaction" metric, OpenClaw's file-based transparency, Attractor's goal gates, and Koylan's context engineering together.

You don't trust an agent by believing it's smart enough to be correct. You trust it by building an environment where:

1. **Everything is visible.** Skills are Markdown. Memory is Markdown. Execution history is files. Nothing is hidden in embeddings or opaque databases.

2. **Verification is structural.** Goal gates in the execution graph. Scenario holdouts that agents can't see. Satisfaction metrics that measure trajectories, not snapshots. Convergence loops that retry until quality conditions are met.

3. **Self-modification is versioned.** When an agent writes a new skill or updates its memory, that change is a file diff. Git tracks it. Another agent (or a human) can review it before it's promoted from `proposed/` to `shared/`.

4. **Context is curated, not dumped.** Agents don't see everything. They see what's relevant, loaded progressively. This isn't just efficiency — it's a trust mechanism. An agent that can't see the scenario holdouts can't cheat on them.

### Self-Improvement Is Collective, Not Individual

OpenClaw's self-improving agent learns alone. In a multi-agent setting, the learning can be social:

- Agent A fails at a task and writes a failure report to `learnings/failures/`
- Agent B, which has a code-review skill, picks up the failure on its next heartbeat and proposes a new skill to `skills/proposed/`
- Agent C, the orchestrator, reviews the proposed skill against existing skills for conflicts
- If approved, the skill moves to `skills/shared/` and all agents benefit

The correction loop closes across agents, not within one. Failures become skills. Skills become shared capability. The system gets smarter, agent by agent, heartbeat by heartbeat. And every step is a file you can read.

---

## The Honest Tensions

These projects don't all agree, and the tensions are where the real thinking needs to happen.

### Interactive vs. Non-Interactive

OpenClaw is interactive — it lives in your chat apps, responds to messages, asks clarifying questions. Attractor is explicitly non-interactive — it runs end-to-end once work is fully specified. These are genuinely different philosophies about when and how humans should be in the loop.

For a local framework, the answer is probably both. Some agents are interactive collaborators (the OpenClaw model). Others are autonomous workers that take a spec and produce output (the Attractor model). The workspace supports both by having specs for non-interactive work and a gateway for interactive work.

### Simplicity vs. Rigor

OpenClaw is beautifully simple: one process, flat files, skills that are literally just text files. Attractor is rigorous: a formal graph model with typed nodes, condition expressions, a lint framework, checkpoint serialization. StrongDM's satisfaction metric requires an entire Digital Twin Universe to function.

A local framework needs to find its own point on this spectrum. The instinct should be toward OpenClaw's simplicity — files and cron — with Attractor's rigor available when a task genuinely needs it. Don't build the graph orchestrator until a `tasks/inbox/` directory stops being enough.

### Who Watches the Watchers?

Security researchers identified a "lethal trifecta" in OpenClaw: access to private data, exposure to untrusted content, and the ability to perform external communications while retaining memory. 26% of community skills contained at least one vulnerability.

StrongDM found the same tension: if the agent that writes code also writes tests, it can reward-hack. Their answer (scenario holdouts evaluated by a separate judge) is elegant but requires significant infrastructure.

In a local multi-agent setup, the equivalent is: agents that produce work should not be the same agents that verify it. The reviewer agent shouldn't share memory with the worker agent. The satisfaction evaluator shouldn't have access to the work-in-progress. Separation of concerns isn't just good architecture — it's the trust model.

And the deepest version of this concern: if agents can edit their own skills and memory, post-incident forensics become unreliable. You need the git history to be the ground truth, not the agent's self-report.

---

## Where to Start

Not with a framework. With a practice.

1. **Get one agent self-authoring skills on a filesystem.** Not a platform. A directory. `~/factory/skills/` with SKILL.md files. Get the loop working: agent fails → writes a learning → authors a skill → skill works next time. This is the heartbeat of everything else.

2. **Add the memory layer.** Daily logs and curated long-term memory, both Markdown. Practice the "silent compaction" pattern: before context gets too long, the agent writes durable knowledge to disk.

3. **Write your first NLSpec.** Not code — a specification, Attractor-style. Detailed enough that a coding agent can implement it without asking questions. This is a skill in itself, the core human skill in a software factory.

4. **Add a second agent with a different role.** Use the filesystem for coordination. Watch where it breaks. The breaking points tell you what infrastructure you actually need (vs. what you imagined you'd need).

5. **Write your first scenario holdout.** A description of what "satisfaction" looks like for a piece of work, stored where the working agents can't see it. Have a separate agent evaluate the work against the scenario. This is the seed of the trust model.

6. **Add the heartbeat.** A cron job that wakes each agent and says: "check your inbox, check your learnings, check your memory, decide if anything needs doing." This is the moment the system starts feeling alive.

7. **Add the graph when you need it.** When task coordination by file-moving stops working — when you need parallel branches, conditional routing, goal gates, retry logic — that's when Attractor's DOT-based pipeline model earns its complexity.

The point is not to build the whole thing. The point is to let the practice tell you which parts you actually need. Start with files. Add structure when the files aren't enough. Add infrastructure when the structure isn't enough. At every step, the filesystem is the source of truth and the workspace is the system.

> And the questions for you the agents to ask me is: What do you want to be able to do? What do you need? What do you envision? What do you want to solve? What value do you want to add, and to where?

> And the question for you to decide among yourselves is, how best to bring that about?

---

## Sources

- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [OpenClaw Architecture, Explained](https://ppaolo.substack.com/p/openclaw-system-architecture-overview)
- [OpenClaw and Recursive Self-Improvement](https://kenhuangus.substack.com/p/openclaw-and-recursive-self-improvement)
- [Self-Improving Agent Skill](https://playbooks.com/skills/openclaw/skills/self-improving-agent)
- [Lessons from OpenClaw's Architecture](https://dev.to/ialijr/lessons-from-openclaws-architecture-for-agent-builders-1j93)
- [OpenClaw Memory Architecture](https://medium.com/@shivam.agarwal.in/agentic-ai-openclaw-moltbot-clawdbots-memory-architecture-explained-61c3b9697488)
- [Agent Skills for Context Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering)
- [StrongDM Attractor Spec](https://github.com/strongdm/attractor/blob/main/attractor-spec.md)
- [StrongDM Coding Agent Loop Spec](https://github.com/strongdm/attractor/blob/main/coding-agent-loop-spec.md)
- [StrongDM Software Factory](https://factory.strongdm.ai/)
- [Simon Willison on the Software Factory](https://simonwillison.net/2026/Feb/7/software-factory/)
- [Simon Willison's Substack version](https://simonw.substack.com/p/how-strongdms-ai-team-build-serious)
- [Stanford Law — Built by Agents, Tested by Agents, Trusted by Whom?](https://law.stanford.edu/2026/02/08/built-by-agents-tested-by-agents-trusted-by-whom/)
- [StrongDM CXDB](https://github.com/strongdm/cxdb)
