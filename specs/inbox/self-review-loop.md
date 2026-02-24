# self-review-loop

## What I'm Seeing
The factory has a universe (`universe/`) containing values, principles, tool capability references, and synthesis documents. It has a growing `memory/` directory where agents record learnings. It has a runtime, a CLI, a pipeline, and several completed specs under its belt. But the only way new intents enter the system is when a human writes one and drops it in `specs/inbox/`. The factory cannot look at itself and ask "what's missing? what's inconsistent? what should I build next?"

## What I Want to See
A new agent or agent-mode (e.g. `factory run reviewer` or an extension of an existing agent) that:

1. Reads the full universe — values, references, synthesis docs
2. Reads the factory's own source code — runtime, CLI, agents config, pipeline structure
3. Reads agent memory files for learnings and patterns
4. Reads completed/verified work in `tasks/verified/` and `specs/archive/` to understand what's been built
5. Identifies gaps, inconsistencies, unmet values, missing capabilities, or improvement opportunities
6. Produces one or more well-formed intent files and drops them in `specs/inbox/`

Each generated intent should follow the standard format (What I'm Seeing / What I Want to See / Why It Matters) and should be specific enough for the Spec agent to process.

This closes the loop. Right now the factory is a straight pipeline: human writes intent → agents process it. With self-review, the factory becomes a cycle: it can observe itself, generate its own work, and improve without waiting for human input. The human shifts from author to curator — reviewing and approving the intents the factory generates rather than writing them from scratch.
