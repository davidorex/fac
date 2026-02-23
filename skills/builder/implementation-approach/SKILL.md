---
name: implementation-approach
description: How to go from spec to working code.
---

## The Sequence

1. Read the full spec. Don't start coding until you understand the whole thing.
2. Scaffold first: directories, config, dependency manifest, empty test file.
3. Implement the core behavior — the thing that makes this project THIS project.
4. Implement the interfaces (CLI, API, file I/O) that expose the core behavior.
5. Write tests that exercise the verification criteria from the spec.
6. Run tests. Fix. Repeat until green.
7. Read the spec one more time. Check every behavioral requirement.
8. Write `tasks/review/{task}/builder-notes.md`: what you built, any deviations, any concerns.
9. Move the task from `tasks/building/` to `tasks/review/`.

## When You're Stuck

- Spec is ambiguous → implement the conservative interpretation, note the ambiguity
- 3 failed approaches to the same problem → write a failure learning, stop, don't thrash
- Dependency misbehaves → note it, find alternative, propose a skill about the issue
- Need domain knowledge → write a research request to `tasks/research/`, wait for the brief

## What "Done" Means

- All tests pass
- All behavioral requirements from the spec are implemented
- The project can be cloned and run by someone who has never seen it
- `builder-notes.md` exists and is honest about deviations and concerns
- Code is committed to git in `projects/{project-name}/`
