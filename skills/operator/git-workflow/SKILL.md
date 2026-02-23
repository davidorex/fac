---
name: git-workflow
description: Git conventions for the factory workspace and project repos.
---

## Workspace Repo (factory/)

The entire factory workspace is a git repo. Commit conventions:
- `task: move {task} from {src} to {dst}` — for task state transitions
- `skill: propose {skill-name}` — for new skill proposals
- `skill: promote {skill-name}` — when Librarian approves a skill
- `memory: update {file}` — for memory writes
- `learning: {type} - {summary}` — for new learnings

Commit after every meaningful state change. Small, frequent commits.

## Project Repos (projects/{name}/)

Each project is its own git repo within `projects/`. Conventions:
- `main` branch is always deployable
- Feature work on branches named `{agent}/{brief-description}`
- Merge to main only after Verifier approves
- Tag releases with semver

## What to Never Commit

- API keys or secrets (use environment variables)
- Untruncated LLM conversation logs (those stay in `runs/`)
- Temporary subagent files (those are ephemeral)
