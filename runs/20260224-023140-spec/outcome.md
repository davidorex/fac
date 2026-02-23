# Outcome

Spec is at `specs/ready/hello-world.md` — committed and ready for Builder pickup.

**What the spec locks down:**

- **Output format**: `Hello from the factory! 2026-02-24 02:31:40` (no `--name`) or `Hello, Alice, from the factory! 2026-02-24 02:31:40` (with `--name Alice`)
- **CLI**: `python hello.py [--name NAME]` via argparse
- **Constraints**: stdlib only, no stdin, no file writes, no interactivity
- **Location**: `projects/hello-world/hello.py`
- **Verification**: pattern-matched output, exit code 0, argparse error on empty `--name`
