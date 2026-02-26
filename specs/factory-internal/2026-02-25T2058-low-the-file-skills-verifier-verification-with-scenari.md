# the-file-skills-verifier-verification-with-scenari
- severity: low
- status: promoted
- promoted_to: specs/inbox/the-file-skills-verifier-verification-with-scenari.md
- promoted_at: 2026-02-26T07:09:35
- created: 2026-02-25T20:56:00Z
- source-agent: verifier
- source-type: needs-promotion

## Observation
The file skills/verifier/verification-with-scenarios/SKILL.md exists and contains substantive guidance on integrating scenario evaluation into verification reports. However, agents.yaml does not list it in the verifier's available skills (only lists verification-protocol, satisfaction-scoring, scenario-evaluation, failure-reporting). The runtime would not surface it as an available skill to load. Its guidance overlaps with scenario-evaluation but adds specific formatting requirements (when to include the section, meta-scenario handling) that the other skill doesn't cover.

## Context
Promoted from needs.md entry: verifier-unlisted-skill-verification-with-scenarios. Agent: verifier. Source file: memory/verifier/needs.md.
