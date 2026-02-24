---
name: dependency-management
description: How to audit, update, and manage dependencies. When to update vs. pin. How to evaluate whether an update is safe.
---

## Auditing Dependencies

On each heartbeat, check for:
- Security advisories: `pip audit` (Python), `npm audit` (Node), `cargo audit` (Rust)
- Outdated packages: `pip list --outdated`, `npm outdated`, `cargo outdated`

Security advisories with CRITICAL or HIGH severity → immediate update, no deferral.
Medium severity → schedule within the current week.
Low severity → batch with next planned update cycle.

## When to Update vs. When to Pin

**Update** when:
- A security advisory affects a current version
- The update is a patch release (X.Y.Z → X.Y.Z+1) with no breaking changes noted
- The project's tests pass after updating

**Pin** when:
- An update introduces breaking API changes the project depends on
- The project is in a stable maintenance state with no active development
- An upstream bug makes the latest version unusable

Document the reason for any pin in a comment next to the pinned version.

## Evaluating Update Safety

Before updating a dependency:
1. Check the changelog for breaking changes
2. Run the project's test suite after updating
3. Check whether any downstream project also depends on this package at a conflicting version

An update that breaks tests is not safe — revert and investigate.

## Dependency Addition

When Builder adds a new dependency (via a spec or maintenance task):
- Verify the package is actively maintained (see `source-evaluation` skill)
- Prefer packages with a clear license (MIT, Apache 2.0, BSD)
- Add it to `pyproject.toml` / `package.json` / `Cargo.toml` with a version constraint, not unpinned
- Run tests after addition to confirm no conflicts
