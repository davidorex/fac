# private-memory-md-has-zero-entries-after-completin

## What I'm Seeing
Private MEMORY.md has zero entries after completing 3+ tasks (hello-world-python, multi-cli-backend-support, no-ephemeral-suggestions). Each new builder session starts cold with no curated knowledge. Builder-specific patterns, factory conventions discovered during implementation, and tool quirks (e.g., the `rm` interactive alias) are not being preserved in the builder's own memory — they exist only in shared KNOWLEDGE.md or git history.

## What I Want to See
This observation should be addressed.
