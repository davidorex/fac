# no-ephemeral-suggestions

## What I'm Seeing
Agents surface workflow observations, friction points, architectural gaps, and improvement suggestions in ephemeral response text. Even with the kernel observation extraction safety net and broadened skill triggers, observations only get persisted to `memory/{agent}/needs.md` as unstructured notes. There's no structured path from "agent notices something" to "factory acts on it." The reviewer just surfaced three real findings (stale universe docs, missing GC pass, daily log gaps) — they made it to needs.md, but needs.md is a flat list with no severity, no lifecycle, and no pipeline integration. Observations die there.

## What I Want to See
Every workflow suggestion, friction observation, or improvement idea from any agent — whether surfaced in response prose, written to needs.md, or extracted by the kernel safety net — becomes a structured spec in `specs/factory-internal/`. Filenames encode date, timestamp, and severity: e.g. `2026-02-25T0817-low-decisions-gc-gap.md`. Severity levels distinguish urgent blockers from nice-to-haves. The factory-internal specs are visible in `factory status` and can enter the normal pipeline (spec → build → verify) or be triaged/dismissed by the operator. Nothing about workflow stays ephemeral.
