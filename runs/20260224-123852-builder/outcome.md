# Outcome

Rebuild of `seed-skill-gaps` complete.

**What was done:** The first build failed at 5/10 — 11 of 14 skills exceeded the 40-line content ceiling while quality, faithfulness, and frontmatter all passed. This rebuild applied editorial compression to all 11 failing skills.

**Final state:**
- All 11 previously-failing skills now within 15–40 lines (31–40 range)
- The 3 passing skills (`researcher-source-evaluation`, `operator-dependency-management`, `operator-monitoring`) untouched
- `tasks/review/seed-skill-gaps.md` updated with rebuild timestamp and `rebuild_of` provenance
- `specs/ready/` cleared of both the spec and the rebuild brief

**Notable compression decisions:**
- `spec-spec-patterns` (was 110 lines): kept only the CLI skeleton as representative; replaced 3 duplicate skeleton types with a 3-line note per rebuild brief guidance
- `builder-tool-use`: `When Tools Fail` section removed entirely — the principle is covered by "check exit codes" in Shell Usage
- `verifier-satisfaction-scoring`: NOT/IS enumeration collapsed to prose; scoring band descriptions reduced to single lines; worked example removed
