Create a new intent and drop it into the factory inbox. Usage: /factory-new <description>

Take the user's description and create an intent file using this format:

```markdown
# <short-kebab-case-name derived from the description>

## What I'm Seeing
<Describe the current state based on what the user said. What exists, what's happening, what's wrong or missing. Observation, not diagnosis.>

## What I Want to See
<Describe the desired end state based on what the user said. What does "done" look like? Not how to get there — just what "there" looks like.>
```

Write it to `/Users/david/Projects/fac/factory/specs/inbox/<name>.md`

Then tell the user the file was created and offer to kick off the Spec agent with:
```bash
cd /Users/david/Projects/fac/factory && .venv/bin/factory run spec
```