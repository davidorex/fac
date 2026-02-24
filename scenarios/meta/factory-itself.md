# Factory Meta-Scenario

A solo developer with a new project idea should be able to describe it in 2-3 sentences, leave, and come back to find: a complete NLSpec they can review, a working implementation, a verification assessment, and a list of what the system learned from building it. The developer's only job is to approve the spec and approve the final result. Everything in between is the factory's problem.

## Evaluation Guidance

This is a directional criterion, not a pass/fail gate. The factory is not yet at meta-scenario fulfillment. When evaluating factory infrastructure changes, ask: does this change move the factory closer to or further from this scenario?

- Closer: changes that increase pipeline autonomy, improve reliability, strengthen self-correction, reduce required human intervention for routine operations
- Further: changes that add manual steps, create ambiguity in the pipeline, lose information between stages, or require human expertise to interpret agent output

Each factory infrastructure task should be evaluated for directional alignment. Document the reasoning.

## Source

Blueprint line 586-589: "Write this into `scenarios/meta/factory-itself.md` on day one."
