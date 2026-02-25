# pipeline-automation

## What I'm Seeing
The factory has all the primitives (spec, builder, verifier, librarian, researcher) and knows the pipeline topology (encoded in `PIPELINE_DOWNSTREAM` and `_compute_next_actions()`). But after every agent run, the factory prints "Next: →" hints and waits for the human to type the next command. The human is acting as the scheduler — manually piping output from one stage to the next. Unix doesn't need me to manually copy output from grep and paste it into sort.

## What I Want to See
A `factory start` command that enters an automated dispatch loop. It checks pipeline state, dispatches the next agent, runs post-execution passes, checks state again, and repeats — until the pipeline is idle or hits a gate that requires human judgment.

Dispatch table in priority order (downstream-first — finish in-progress work before starting new):

1. `tasks/review/` has files → run verifier
2. `tasks/verified/` has files → run docs (librarian)
3. `tasks/failed/` has files → run builder rebuild
4. `specs/ready/` has files → run builder
5. `specs/drafting/` + research done + decisions resolved → advance
6. `tasks/research/` has files → run researcher
7. `factory-internal/` has low severity → auto-promote to inbox
8. `specs/inbox/` has files → run spec

Gates (loop stops, WhatsApp notification sent):
- Unresolved decision entries in `tasks/decisions/`
- Critical/high observations in `factory-internal/`
- Agent crash or timeout
- Rebuild retry limit hit (prevent infinite spec→build→fail→rebuild loops)

What stays manual: `factory run {agent}` for direct override, `factory decide` for decision gates, `factory triage` for critical/high observations, and `factory start` itself — the human starts the pipeline.
