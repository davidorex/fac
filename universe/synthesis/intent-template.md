# Intent Format

When you want the factory to build something, write a file to `specs/inbox/` with two sections:

```markdown
# [working title]

## What I'm Seeing
[Describe the current state. What exists, what's happening, what's wrong or missing.
This is observation, not diagnosis. Ground it in what's actually there.]

## What I Want to See
[Describe the end state. What does it look like when this is done?
Not how to get there — just what "there" looks like.]
```

The gap between the two sections is what the factory builds.

## Why This Shape

Spec's job is to turn fuzzy intent into a precise NLSpec. The more grounded your observations are, the less Spec has to guess about context. The more concrete your desired end state, the less ambiguity in the spec it produces.

You don't need to know the solution. You don't need to specify technology, approach, or architecture. You're describing a transformation: from what is, to what should be.

## Examples

### New project (nothing exists yet)

```markdown
# markdown-watcher

## What I'm Seeing
I have a directory of markdown files that I edit by hand.
When I want to share them, I manually convert each one to HTML.

## What I Want to See
A process that watches the directory and converts changed files to HTML automatically.
Output goes to a parallel directory. Preserves relative links between files.
```

### Process fix (something's broken)

```markdown
# spec-archiving

## What I'm Seeing
When Builder picks up a spec from specs/ready/, the spec disappears.
By the time Verifier runs, there's nothing to compare against.
Verifier flagged this on the hello-world task.

## What I Want to See
Specs persist through the entire pipeline lifecycle.
Verifier can always read the original spec when evaluating work.
Archived specs accumulate as a reference library.
```

### Self-improvement (the factory fixes itself)

```markdown
# factory-feedback-loop

## What I'm Seeing
Verifier catches process issues but writes them into task reports.
No agent reads completed task reports for process-level observations.
The same problem will recur on the next task.

## What I Want to See
Process issues flow back into the factory's improvement cycle.
When Verifier notes a gap, it becomes a learning.
Learnings become skill updates. Same mistake doesn't happen twice.
```

### Capability extension

```markdown
# factory-new-command

## What I'm Seeing
To start a new task, I have to manually create a markdown file
in specs/inbox/ and know the right format. There's no CLI shortcut.

## What I Want to See
I type `factory new "description of what I want"` and it creates
the intent file in specs/inbox/ for me, optionally kicking off
the spec agent immediately.
```
