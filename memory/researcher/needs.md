# Researcher — Needs

## researcher-role-mechanism-misalignment
- status: open
- created: 2026-02-24T21:13:51Z
- category: observation
- blocked: Role description says "surface what the factory doesn't know yet" and "your voice matters — say something," implying proactive research capability. But the pipeline structure is entirely reactive — I wait for files to appear in tasks/research/. My heartbeat (0 9 * * *) checks for pending requests, but if none exist, there is no mechanism for me to initiate research on questions I identify as important. The proactive voice the role promises has no channel.
- context: First reflection pass. Examined role description against actual pipeline mechanics.

### Exact Change
Two possible approaches (human decides):
1. Add a proactive research channel — e.g., during heartbeat, I scan specs/ready/ or specs/drafting/ for technology questions that would benefit from research, and self-file research tasks.
2. Narrow the role description to match the reactive pipeline — remove the "surface what the factory doesn't know yet" language if proactive research isn't intended.
Option 1 adds value but increases agent activity. Option 2 is simpler but loses the proactive intelligence function.

## researcher-source-hierarchy-divergence
- status: open
- created: 2026-02-24T21:13:51Z
- category: observation
- blocked: skills/researcher/research-approach/SKILL.md (lines 31-38) and skills/researcher/source-evaluation/SKILL.md both define source hierarchies, but they diverge. research-approach lists 6 tiers including "Conference talks and technical papers" (tier 4) and "Community forums" (tier 5). source-evaluation lists 5 tiers, omits conference talks entirely, and names tier 4 "Stack Overflow / community Q&A." When both skills are loaded simultaneously, the applicable hierarchy is ambiguous.
- context: First reflection pass. Read both skill files and compared structures.

### Exact Change
Refactor so the hierarchy lives in one place. source-evaluation should be the canonical definition (it's the judgment skill). research-approach should reference source-evaluation for the hierarchy rather than embedding its own version. Alternatively, reconcile the two lists into one and update both files.
