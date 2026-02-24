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

## Web API

```
## Overview
{Service purpose and primary consumers}

## Behavioral Requirements
- Endpoint: {METHOD /path} — {what it does}
- Authentication: {mechanism}
- Error handling: {approach}

## Interface Boundaries
### Request/response schemas
{JSON schemas or typed examples}
### Dependencies
{External services, databases}

## Constraints
- {Rate limits, auth requirements, backwards compat rules}

## Verification Criteria
- {Endpoint returns expected schema for valid input}
- {Endpoint returns appropriate error for invalid input}
```

## Data Pipeline

```
## Overview
{Source → transformation → destination}

## Behavioral Requirements
- Reads from: {source format/location}
- Transforms: {what changes}
- Writes to: {destination format/location}
- Handles: {missing data, schema mismatches, duplicates}

## Interface Boundaries
### Input schema
### Output schema
### Error handling

## Constraints
- {Volume expectations, latency requirements}

## Verification Criteria
- {Given input X, output matches Y}
- {Error cases produce expected behavior}
```

## Library / Module

```
## Overview
{What this library does and who uses it}

## Behavioral Requirements
- Public API: {function/class signatures and behaviors}
- Error contracts: {what exceptions are raised and when}

## Interface Boundaries
### Public API
{Complete signatures with type annotations}
### What this library does NOT do

## Constraints
- {Dependency constraints, Python version}

## Verification Criteria
- {API contracts hold}
- {Error cases raise expected exceptions}
```

## Filling in the Skeleton

- Every spec must have Verification Criteria that are testable without human judgment
- Behavioral Requirements describe what the system does, not how it does it
- Interface Boundaries are contracts — be precise about schemas and types
- Constraints are hard limits — if something is merely a preference, say so
