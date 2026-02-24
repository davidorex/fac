---
name: failure-reporting
description: How to write a useful failure report. Not "it's wrong" — what's wrong, why it matters, what the spec says, what the code does, and a path forward.
---

## Purpose of a Failure Report

A failure report exists to enable resolution — not to document that something failed.
It must contain enough information for Builder (or a human) to understand and fix the
gap without having to re-read the spec and re-examine the code from scratch.

## Required Sections

Every failure report must include:

**Summary** — One paragraph: what was verified, what the overall finding is, and the
score. Do not make this a list of failures — that belongs in the artifact assessment.

**Artifact-by-Artifact Assessment** — For each deliverable the spec describes:
- What the spec requires (quote it if brief)
- What the implementation does
- Whether this criterion passes, partially passes, or fails

**Satisfaction Score** — The numeric score with reasoning (see `satisfaction-scoring` skill).

**Path to Resolution** — Concrete steps Builder would need to take to bring the
score above the passing threshold. Not vague guidance — specific changes.

**Generalizable Learning** — The class of failure, why it occurred, what future
specs or implementations should do differently. See `verification-protocol` skill.

## What Makes a Good Failure Report

Good:
- "The spec requires `parser.error()` for empty name strings (Verification Criteria #3).
  The implementation accepts empty strings silently and prints 'Hello, '. Fix: add
  `if not args.name: parser.error('name cannot be empty')` after parsing."

Poor:
- "The error handling is wrong."

The difference is specificity. A poor failure report sends Builder back to the spec.
A good failure report tells Builder exactly what to change.

