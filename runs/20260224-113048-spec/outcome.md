# Outcome

Specs written and promoted. Here's the heartbeat summary:

**Processed 3 reviewer-generated intents → 3 NLSpecs now in `specs/ready/`:**

1. **spec-pipeline-cleanup** — Runtime post-execution cleanup that enforces single-stage invariant across the spec pipeline. Removes upstream copies when a spec advances downstream. Includes `factory cleanup-specs --dry-run` CLI command. Solves the stale-file problem at the runtime level without requiring agents.yaml access changes.

2. **failure-learning-convention** — Verifier failure reports gain a required `## Generalizable Learning` section. Runtime extracts the section to `learnings/failures/` automatically (sidestepping Verifier's lack of write access to learnings/). Also defines the re-verification path: human moves task from `tasks/failed/` → `tasks/review/`, Verifier picks up on next heartbeat.

3. **seed-skill-gaps** — 14 missing seed skills written to `skills/proposed/` with agent-prefixed naming for Librarian routing. Content derived from the factory blueprint's "Seeded with:" descriptions. Each 15-40 lines of behavioral guidance.

**Noted issues:**
- 4 stale files remain in `specs/inbox/` and `specs/drafting/` from prior work (pipeline-next-step, self-review-loop). I can't delete them due to access constraints. The spec-pipeline-cleanup spec, once built, will resolve this automatically.
- Librarian's `can_write` doesn't include `skills/{agent}/` directories — promoting the 14 seed skills from `skills/proposed/` to their target locations will require either expanding Librarian's access or human intervention.
