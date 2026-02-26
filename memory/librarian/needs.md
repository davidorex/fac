# Librarian Needs

## librarian-core-skills-not-always-loaded
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T2101-low-the-three-skills-most-central-to-my-function-knowl.md
- created: 2026-02-25T20:58:56
- category: observation
- blocked: The three skills most central to my function — `knowledge-curation`, `pattern-detection`, `memory-hygiene` — are listed as `available` rather than `always`. The `knowledge-curation` skill itself begins "On every heartbeat, check `skills/proposed/`..." indicating it is expected to be active every heartbeat. If available skills must be explicitly activated and the heartbeat prompt does not remind the agent to load them, routine curation runs may operate on implicit understanding rather than the documented protocol. The omission is silent — no error, just potentially unguided curation.
- context: Reflection pass 2026-02-25. Noticed the gap between "available" classification and the "every heartbeat" instruction inside the skill content.

### Exact Change
In `agents.yaml`, move `librarian/knowledge-curation`, `librarian/pattern-detection`, and `librarian/memory-hygiene` from `available:` to `always:` for the librarian agent. These three skills collectively define what a curation pass is. Keeping them in `available` is appropriate for occasional-use skills, not for the agent's core operating procedure.

---

## librarian-role-description-factory-needs-ambiguity
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T2101-high-the-role-description-ends-with-surface-knowledge-g.md
- created: 2026-02-25T20:58:56
- category: observation
- blocked: The role description ends with "surface knowledge gaps to factory needs for the human." Since the `no-ephemeral-suggestions` spec shipped, `factory needs` is a specific CLI command that surfaces only blockers — observations no longer appear there. Knowledge gaps now surface via the `specs/factory-internal/` observation pipeline and are managed with `factory triage`. The current role description points to a dead-end path and would mislead a new operator reading agents.yaml.
- context: Reflection pass 2026-02-25. Cross-checked role wording against the established Human-Action-Needed System convention in KNOWLEDGE.md.

### Exact Change
In `agents.yaml`, update the librarian role description to replace "surface knowledge gaps to factory needs for the human" with "surface knowledge gaps to the operator via the observation pipeline." This aligns the role description with current `factory needs` semantics.
