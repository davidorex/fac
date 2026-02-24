---
name: refactorability-first
description: Ship working, build changeable. When implementing decisions made under ambiguity, build seams so the decision can be changed without rewriting.
---

## Ship Working, Build Changeable

Intent is king. A working demo that meets intent trumps a perfect architecture that doesn't exist. But:

- Working does not mean brittle
- Demo does not mean prototype to throw away
- Smart construction now prevents rewrite later

## Refactorability Patterns

When a spec contains decisions made under ambiguity (auto-resolved soft gates, or operator decisions that might change), apply these patterns at the decision boundary:

1. **Interface boundaries.** Where the ambiguous decision lives, build a seam. The rest of the code talks to the interface, not the implementation.

2. **Parameterized choices.** Hardcoded choices are sins. Parameterized choices are features. A config flag, an enum, an argument — anything that makes swapping the choice a one-line change.

3. **Test behavior, not implementation.** Tests are the contract that survives refactoring. Assert "output is correct" not "streaming parser was called." Tests should pass regardless of which option was chosen.

4. **Own your dependencies.** Wrap external APIs so you can swap providers. The factory's own multi-backend abstraction is a living example of this pattern.

5. **No global state at decision boundaries.** Makes testing hard, makes refactoring impossible. Pass the choice in, don't reach out for it.

## Builder Notes

When Builder implements work that includes auto-resolved decisions, write `builder-notes.md` alongside the task in `tasks/review/`. This file documents:

- Each decision made under ambiguity
- The seam where the decision lives in code
- The refactor trigger (condition under which the decision should be revisited)
- The estimated cost to change (low/medium/high)

The Verifier reads builder-notes to verify that seams exist and decisions are properly parameterized. The operator reads builder-notes to review auto-resolved decisions asynchronously.

## The Permission

You have permission to decide under ambiguity. The decision-heuristic skill tells you when and how. This skill tells you how to build the result so that changing your mind is cheap.

The contract: if the cost-to-change is documented as LOW and the seam exists, the decision was responsibly made. If the operator overrides, the rebuild is bounded.
