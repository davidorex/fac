# Researcher — Needs

## researcher-empty-private-memory
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T2048-low-private-memory-md-is-empty-after-two-substantive-r.md
- created: 2026-02-25T20:45:00Z
- category: observation
- blocked: Private MEMORY.md is empty after two substantive research runs. Durable patterns (universe docs need empirical verification, kimi-cli specifics, self-correction between v1/v2) exist only in daily logs and delivered briefs. If daily logs grow long, these patterns drop out of context. No skill or convention specifies when researcher should write to MEMORY.md vs. daily log vs. learnings — the self-improvement skill covers learnings and proposed skills but not private memory curation.
- context: Reflection pass, 2026-02-25. Researcher has completed two kimi-cli research tasks across two days but MEMORY.md remains at its initialization state.

### Exact Change
Two options: (1) Add guidance to the `shared/self-improvement` skill about when to write to private MEMORY.md — after every research delivery, persist any reusable patterns. (2) Add a researcher-specific skill `researcher/memory-hygiene` that specifies the curation trigger. Option 1 is better because every agent has the same gap. Immediate corrective action: researcher will populate its own MEMORY.md now.

## researcher-no-universe-correction-loop
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T2048-low-caught-5-inaccuracies-in-universe-reference-tool-c.md
- created: 2026-02-25T20:45:00Z
- category: observation
- blocked: Caught 5 inaccuracies in `universe/reference/tool-capabilities.md` during kimi-cli research. universe/ is read-only for all agents. Corrections live in the delivered research brief (a one-time deliverable consumed and discarded by the spec agent) and in daily logs (append-only, not indexed). No agent can write to universe/. No mechanism exists to feed verified corrections back to reference docs. Known inaccuracies persist until the human manually updates them.
- context: kimi-cli research v1 and v2 (2026-02-24, 2026-02-25). Reference doc corrections documented in `tasks/research-done/spec-kimi-cli-interface-v2.md` § "Reference Doc Corrections" but nowhere durable or discoverable.

### Exact Change
Options: (a) Create a `universe/errata/` directory that agents CAN write to, with structured correction entries that the human reviews before applying. (b) Researcher writes a correction entry to `learnings/corrections/` which Librarian could propagate to `memory/shared/KNOWLEDGE.md` under a "Known Reference Doc Issues" section. Option (b) works within current access scopes. Option (a) is cleaner but requires scope changes.

## researcher-brief-format-assumes-comparison
- status: promoted
- promoted_to: specs/factory-internal/2026-02-25T2048-low-the-researcher-recommendation-format-skill-prescri.md
- created: 2026-02-25T20:45:00Z
- category: observation
- blocked: The `researcher/recommendation-format` skill prescribes a Question -> Options -> Recommendation -> Reasoning -> Trade-offs -> Confidence -> Sources structure with a 500-word limit. The kimi-cli research was an empirical investigation ("what are the verified interface details?"), not a comparison question. The delivered brief was effective but used a different structure and exceeded 500 words significantly. The skill doesn't acknowledge investigation-type briefs, which may be the more common research pattern for this factory (verify claims, characterize tools, map interfaces).
- context: Reflection pass, 2026-02-25. The v2 kimi-cli brief in `tasks/research-done/spec-kimi-cli-interface-v2.md` deviated from the recommendation-format skill and was better for it.

### Exact Change
Either: (a) Expand `researcher/recommendation-format` to include an "Investigation Brief" variant with its own structure (Methodology -> Findings -> Corrections -> Implications -> Confidence -> Sources) and a higher word budget. Or (b) Create a separate `researcher/investigation-format` skill. The investigation variant needs: a methodology section (how findings were verified), a corrections section (what was wrong in prior sources), and no forced Options/Recommendation sections.
