# Scenario 6: The Meta-Test

**Title:** The factory builds a feature of itself

**Story:** The developer wants to add a `factory dashboard` command that shows a live view of workspace status.

**Expected trajectory:**

The developer writes the intent. Spec requests research on terminal dashboard libraries. Researcher evaluates `blessed`, `ink`, and `bubbletea`, recommends one. Spec writes the NLSpec referencing the factory runtime spec from `universe/synthesis/factory-blueprint.md` for workspace structure.

Builder implements it, consulting `universe/` for the workspace layout it needs to render. Verifier evaluates it against a holdout scenario (this one) describing what the dashboard should show: agent names with last-run times, task pipeline counts, context budget of most recent run, and recent learnings.

**Satisfaction criteria:** The factory successfully used its own documentation (in `universe/`) to build a feature for itself. The recursive loop works: the factory's reference material informed a spec, which informed an implementation, which was verified against a holdout.
