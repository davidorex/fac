# Factory — Architectural Metaphor

The factory is an operating system. Use this mapping as a heuristic for meta-design decisions.

| OS Concept | Factory Layer | Concrete |
|---|---|---|
| Kernel | `runtime/factory_runtime/` | cli.py, llm.py, context.py, config.py, access.py — scheduling, access control, cleanup, process lifecycle |
| Bus | Filesystem directory protocol | `specs/`, `tasks/`, `memory/` — IPC via files in known locations |
| Lib | Skills + conventions + universe | `skills/shared/`, `universe/` — shared libraries linked at invocation |
| Apps | Agents | Userspace processes with permissions, private memory, defined I/O |
| I/O | Directory transitions | inbox→drafting→ready, research→research-done, building→review→verified — pipes between processes |
| Gates | Decision points requiring human input | Interrupts — process blocks, signals user, waits for response |

## Where Does It Belong?

- Process-to-process coordination → bus (filesystem conventions)
- Lifecycle management, cleanup, access enforcement → kernel (runtime code)
- Reusable agent behavior → lib (skills)
- New capability → app (agent or agent skill)
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

## Project Registration

Any directory can be a factory project. Run `factory init-project` from within it to write a `.factory` marker file pointing to the factory workspace. After that, all `factory` commands work from within that directory. The CLI resolves upward (like `.git`) to find the marker.

## WhatsApp Bridge (NanoClaw IPC)

All agents can send WhatsApp notifications via `notifications/` (symlink to NanoClaw IPC). The kernel automatically sends a notification after every agent run (skipping idle NO_REPLY heartbeats) with the agent's response summary and computed next actions. Inbound: NanoClaw can drop intents into `specs/inbox/` via its `factory-inbox` skill.

## Decision Gates: Soft vs Hard

When an agent hits ambiguity, the kernel classifies by reversibility and impact:

- **Soft gate** (`reversibility: high` + `impact: implementation|cosmetic`): kernel auto-resolves. Agent picks the more-flexible option, builds a seam, documents the trigger. Work continues. Operator reviews asynchronously.
- **Hard gate** (`reversibility: low` OR `impact: governance`): kernel blocks. Writes structured decision request to `tasks/decisions/`. Operator responds via `factory decide`. Pipeline resumes.

## Kernel GC Passes

The kernel runs garbage collection after every agent execution:
- `cleanup-specs`: removes upstream spec copies when downstream exists
- `cleanup-tasks`: removes tasks/review/ copies when verified/failed exists
- `cleanup-research`: removes tasks/research/ copies when tasks/research-done/ exists
