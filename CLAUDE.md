# Factory — Architectural Metaphor

The factory is an operating system. Use this mapping as a heuristic for meta-design decisions.

| OS Concept | Factory Layer | Concrete |
|---|---|---|
| Kernel | `runtime/factory_runtime/` | cli.py, llm.py, context.py, config.py, access.py, permissions.py, apps.py — scheduling, access control, cleanup, process lifecycle |
| Bus | Filesystem directory protocol | `specs/`, `tasks/`, `memory/` — IPC via files in known locations |
| Lib | Skills + conventions + universe | `skills/shared/`, `universe/` — shared libraries linked at invocation |
| Chips | Agents | Persistent processes with permissions, private memory, defined I/O |
| Apps | Workflow definitions in `apps/` | YAML-declared pipelines, dispatch rules, checkpoints, strategies (e.g. `apps/gsd.yaml`) |
| I/O | Directory transitions | inbox→drafting→ready, research→research-done, planning→building→review→verified — pipes between processes |
| Gates | Decision points requiring human input | Interrupts — process blocks, signals user, waits for response |

## Where Does It Belong?

- Process-to-process coordination → bus (filesystem conventions)
- Lifecycle management, cleanup, access enforcement → kernel (runtime code)
- Reusable agent behavior → lib (skills)
- New agent capability → chip (agent or agent skill)
- New workflow over existing agents → app (YAML in `apps/`)
- Pipeline stops for human input → gate (interrupt mechanism)

## Operator Model

The human is not a user of the system — the human is the **system operator**. They respond to interrupts, make policy decisions, provision resources, and drop work into the input buffer.

| Console Command | OS Equivalent | Purpose |
|---|---|---|
| `factory status` | `top`/`htop` | Process monitor — what's running, blocked, queued |
| `factory run AGENT [SPEC]` | Process scheduler | Dispatch a specific agent, optionally targeting a spec |
| `factory advance SPEC` | Context-aware dispatch | Gather research + decisions, send to right agent for finalization |
| `factory decide SPEC` | Interrupt handler | Respond to hard gates — `--entry ID --answer CHOICE` |
| `factory needs` | `dmesg` | Kernel message buffer — agent blockers and observations |
| `factory init-project` | `mount` | Register current directory as a factory project (writes `.factory` marker) |
| `factory rebuild TASK` | Process restart | Re-queue failed work with versioned failure report |
| `factory resolve TASK` | Manual interrupt clear | Mark a failed task as resolved without rebuild |
| `factory reflect [AGENT]` | Self-diagnostic | Agents examine own state, surface observations |
| `factory perms [--agent]` | `ls -la` | Unix-style permissions model — groups, resources, modes |
| `factory apps [--app]` | App store | List registered apps and their pipeline definitions |

## Project Registration

Any directory can be a factory project. Run `factory init-project` from within it to write a `.factory` marker file pointing to the factory workspace. After that, all `factory` commands work from within that directory. The CLI resolves upward (like `.git`) to find the marker.

## WhatsApp Bridge (NanoClaw IPC)

All agents can send WhatsApp notifications via `notifications/` (symlink to NanoClaw IPC). The kernel automatically sends a notification after every agent run (skipping idle NO_REPLY heartbeats) with the agent's response summary and computed next actions. Inbound: NanoClaw can drop intents into `specs/inbox/` via its `factory-inbox` skill.

## Decision Gates: Soft vs Hard

When an agent hits ambiguity, the kernel classifies by reversibility and impact:

- **Soft gate** (`reversibility: high` + `impact: implementation|cosmetic`): kernel auto-resolves. Agent picks the more-flexible option, builds a seam, documents the trigger. Work continues. Operator reviews asynchronously.
- **Hard gate** (`reversibility: low` OR `impact: governance`): kernel blocks. Writes structured decision request to `tasks/decisions/`. Operator responds via `factory decide`. Pipeline resumes.

## Apps: Declarative Workflow Definitions

Apps are YAML files in `apps/` that declare workflows over the existing agents and bus. Each app can introduce new pipeline stages, dispatch rules, checkpoint types, and execution strategies. The kernel reads these definitions to determine how work flows through the system.

- `apps/gsd.yaml` — Project execution app. Adds a `tasks/planning/` stage between `specs/ready/` and `tasks/building/`. Builder produces a plan artifact; verifier validates before execution. Plans carry checkpoint declarations that the kernel reads to select autonomous, segmented, or decision-dependent execution.
- To add a new workflow, drop a new YAML file in `apps/`. Same kernel, same bus, same agents — different orchestration.
- To change how a workflow works, edit its YAML file.

## Kernel GC Passes

The kernel runs garbage collection after every agent execution:
- `cleanup-specs`: removes upstream spec copies when downstream exists
- `cleanup-tasks`: removes tasks/review/ copies when verified/failed exists
- `cleanup-research`: removes tasks/research/ copies when tasks/research-done/ exists
