---
name: spec-patterns
description: Skeleton NLSpec structures for common project types. Use these as starting frames, not rigid templates.
---

## CLI Tool

```
## Overview
{What it does in one sentence}

## Behavioral Requirements
- Accepts {arguments/flags}
- Outputs {format} to {stdout/file}
- Handles {error cases} with {behavior}

## Interface Boundaries
### CLI interface
{Exact command syntax and flag descriptions}
### Output format
{Schema or example output}

## Constraints
- No external dependencies beyond stdlib (or: depends on {libraries})
- Must run on Python 3.10+

## Verification Criteria
- {Concrete, testable condition}
- {Concrete, testable condition}
```

The same structure — Overview, Behavioral Requirements, Interface Boundaries, Constraints,
Verification Criteria — applies to all project types (Web APIs, data pipelines, libraries).
Adapt section contents to fit the project type's conventions and vocabulary.

## Filling in the Skeleton

- Every spec must have Verification Criteria that are testable without human judgment
- Behavioral Requirements describe what the system does, not how it does it
- Interface Boundaries are contracts — be precise about schemas and types
- Constraints are hard limits — if something is merely a preference, say so
