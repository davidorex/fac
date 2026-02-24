---
name: tool-use
description: How to use the filesystem, shell, and git. Builder's tool vocabulary and conventions for interacting with the development environment.
---

## Filesystem Conventions

- All paths are relative to the workspace root (`/Users/david/Projects/fac/factory`)
- Write implementation artifacts to `projects/{project-name}/`
- Write work-in-progress notes to `tasks/building/{task-name}.md`
- Move completed work to `tasks/review/{task-name}.md` — this is the signal to Verifier
- Never write to `tasks/verified/`, `tasks/failed/`, or `scenarios/`

## Shell Usage

- Use shell for: running tests, checking file existence, git operations
- Prefer Python stdlib over shell for file manipulation within scripts
- Always quote paths that may contain spaces
- Check exit codes — a silent failure is worse than a loud one
- When running `pip install` or similar, work within the project's virtual environment

## Git Conventions

- Commit after each meaningful state change (not after every file write)
- Commit messages: specific, present tense, describe the intent not the mechanism
  - Good: "Add argparse validation that rejects empty name strings"
  - Avoid: "Fix bug", "Update code", "WIP"
- Stage specific files rather than `git add -A`
- Never force-push or amend a commit that has already been used as a checkpoint

## File Operations

- Read the file before editing it — do not assume its content
- When creating a new project directory, verify the parent exists first
- Do not delete files unless the spec explicitly requires deletion
- Prefer editing existing files over replacing them wholesale

## Python Project Conventions

- Use `pyproject.toml` for new Python projects (not `setup.py`)
- Virtual environments live at `projects/{project-name}/.venv/`
- Tests live at `projects/{project-name}/tests/`
- Keep stdlib-only implementations unless dependencies are specified in the spec

