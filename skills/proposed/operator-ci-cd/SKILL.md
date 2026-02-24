---
name: ci-cd
description: How to set up and maintain CI/CD per stack. GitHub Actions patterns, testing configurations, deployment scripts.
---

## Setting Up CI for a New Project

When Builder completes a new project, Operator sets up CI. Standard checklist:

1. Identify the stack (Python, TypeScript, Rust, etc.)
2. Create `.github/workflows/ci.yml` with the appropriate test runner
3. Verify the workflow triggers on `push` to main and on pull requests
4. Confirm the test command matches the project's actual test runner

## GitHub Actions Patterns by Stack

**Python**
```yaml
- uses: actions/setup-python@v4
  with: { python-version: "3.11" }
- run: pip install -e ".[dev]"
- run: pytest
```

**Node / TypeScript**
```yaml
- uses: actions/setup-node@v4
  with: { node-version: "20" }
- run: npm ci
- run: npm test
```

**Rust**
```yaml
- uses: dtolnay/rust-toolchain@stable
- run: cargo test
```

## Maintaining Existing CI

On each heartbeat, check:
- Are any CI runs failing on main? (check via `gh run list --branch main`)
- Are workflows pinned to outdated action versions?
- Are test commands still correct after dependency updates?

A failing main branch is the highest priority maintenance task. Address before
any other operational work.

## Deployment

Deployment scripts live in `projects/{project-name}/.factory/deploy.sh` or
as a GitHub Actions workflow. Operator owns these scripts but does not invoke
deployments without explicit human authorization.

Before writing a deployment script, confirm:
- Target environment (local, staging, production)
- Authentication method
- Rollback procedure
