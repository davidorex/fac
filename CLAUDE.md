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
| `factory decide` | Interrupt handler console | Respond to hard gates — read context, make call, resume |
| `factory needs` | `dmesg` | Kernel message buffer — hardware-level issues |
| `factory run` | Process scheduler | Dispatch a specific process |

## Decision Gates: Soft vs Hard

When an agent hits ambiguity, the kernel classifies by reversibility and impact:

- **Soft gate** (`reversibility: high` + `impact: implementation|cosmetic`): kernel auto-resolves. Agent picks the more-flexible option, builds a seam, documents the trigger. Work continues. Operator reviews asynchronously.
- **Hard gate** (`reversibility: low` OR `impact: governance`): kernel blocks. Writes structured decision request to `tasks/decisions/`. Operator responds via `factory decide`. Pipeline resumes.

## Kernel GC Passes

The kernel runs garbage collection after every agent execution:
- `cleanup-specs`: removes upstream spec copies when downstream exists
- `cleanup-tasks`: removes tasks/review/ copies when verified/failed exists
- `cleanup-research`: removes tasks/research/ copies when tasks/research-done/ exists
