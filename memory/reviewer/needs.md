# Reviewer — Needs and Observations

## reviewer-private-memory-access-inaccuracy
- status: open
- created: 2026-02-24T21:29:00Z
- category: observation
- blocked: My MEMORY.md access section states "Cannot access: scenarios/, tasks/building/, projects/" — but `projects/` is in my `can_read` list in agents.yaml. It also lists `can_read` as a subset of reality, omitting the full `memory/` scope (lists only `memory/shared/`) and omitting `runtime/`. When I re-read my own memory at the start of each session, I receive a narrower self-model than my actual configuration allows. This creates risk of self-limiting — not reading directories I'm permitted to read because my memory says I can't.
- context: Reflection pass 2026-02-24. Compared MEMORY.md access section against agents.yaml can_read/cannot_access. Three discrepancies found.

### Exact Change
Update MEMORY.md access section to match agents.yaml:
```
- Read: universe/, memory/, learnings/, specs/, tasks/verified/, tasks/failed/, skills/, projects/, runtime/
- Write: specs/inbox/, memory/reviewer/, memory/daily/reviewer/, skills/proposed/
- Cannot access: scenarios/, tasks/building/
```
I can make this change myself since memory/reviewer/ is in my write scope.

---

## reviewer-decomposition-always-loaded-unused
- status: open
- created: 2026-02-24T21:29:00Z
- category: observation
- blocked: `shared/decomposition` is always-loaded but has never been activated across 5 review runs and 7 generated intents. Review work is single-pass by nature — I scan directories, compare state, write intents. No review has had 3+ independent facets suitable for parallel subagent work. The skill's own criteria for activation have never been met. This matches observations from spec, builder, and verifier (all three independently noted the same unused overhead in their reflection passes).
- context: Reflection pass 2026-02-24. Cross-referenced my daily log entries — decomposition never referenced, no subagent tasks created. Four of six agents have now independently identified this as overhead.

### Exact Change
Move `shared/decomposition` from `skills.always` to `skills.available` in reviewer's agents.yaml config. Given that spec, builder, and verifier have all independently made the same observation, consider doing this for all four agents simultaneously. Decomposition may become relevant for complex external project work — keeping it available but not always-loaded preserves the option without the cost.

---

## reviewer-self-improvement-disconnected-from-protocol
- status: open
- created: 2026-02-24T21:29:00Z
- category: observation
- blocked: The `shared/self-improvement` skill (always loaded) instructs agents to write learnings to `learnings/` and propose skills to `skills/proposed/`. My `review-protocol` skill has no step for either activity. All my outputs go to `specs/inbox/` as intents. Across 5 review runs I have never written a learning or proposed a skill, despite having write access to both `learnings/` (implicitly, through the skill instruction) and `skills/proposed/` (explicitly). The two always-loaded skills — self-improvement and review-protocol — are structurally disconnected in my workflow. This means patterns I observe repeatedly (e.g., the 5-deferral shared-memory observation) never become codified learnings that other agents could consume.
- context: Reflection pass 2026-02-24. The self-improvement skill says "write a learning" when you "notice a pattern across multiple tasks." I noticed the memory staleness pattern across 5 consecutive reviews but never wrote a learning — I wrote an intent instead. These are different outputs with different consumers. An intent goes to the human via the spec pipeline. A learning goes to the Librarian for potential skill evolution. My protocol routes everything to intents, bypassing the learning system entirely.

### Exact Change
Add a step to review-protocol between Step 4 (Generate Intent Files) and Step 5 (Daily Log Entry):

"**Step 4.5: Learning Extraction** — If this review identified a pattern across 2+ runs (same category of gap, same deferred observation, same type of pipeline failure), write a discovery to `learnings/discoveries/{date}-{summary}.md`. Intents solve specific gaps; learnings capture the meta-pattern for future factory intelligence."

---

## reviewer-deduplication-filename-only
- status: open
- created: 2026-02-24T21:29:00Z
- category: observation
- blocked: My deduplication check (review-protocol Step 1) compares intent slugs against filenames in specs/inbox/, drafting/, ready/, archive/. But my intents frequently get addressed by differently-named specs: `failure-learning-gap` → `failure-learning-convention`, `inbox-cleanup-convention` → `spec-pipeline-cleanup`. This caused two stale files in specs/inbox/ that persisted from 12:08 to 20:26 (~8 hours), which I deferred 4 times as "not worth an intent." The spec agent's needs.md confirms downstream impact — they now perform significant triage of my intents to check whether the underlying issue has already been resolved by a differently-named spec. My filename-only dedup creates work for the spec agent.
- context: Reflection pass 2026-02-24. Evidence: daily log entries at 12:08, 12:56, 14:45, 20:26 all note the same two stale files. Spec agent's `spec-role-description-missing-triage` observation explicitly attributes triage overhead to this pattern.

### Exact Change
Enhance review-protocol Step 1 to include semantic dedup, not just filename matching: after checking filenames, also scan the `## What I'm Seeing` sections of existing specs/archive/ entries for topical overlap with any candidate intent. If an archived spec addresses the same underlying concern (even under a different name), note it as "addressed by {archive-filename}" in the daily log and do not generate the intent. This is within my own protocol — I can propose a skill update to `skills/proposed/` with the revised review-protocol.

---

## reviewer-deferral-escalation-unformalized
- status: open
- created: 2026-02-24T21:29:00Z
- category: observation
- blocked: My protocol has no formal mechanism for when deferred observations should escalate to intents. The shared-memory staleness was deferred 5 consecutive times across ~9 hours (11:25, 12:08, 12:56, 14:45, 20:26) before I generated an intent. Each individual deferral was well-reasoned ("operational, not structural"), but cumulatively I was too patient. The escalation only happened because at 14:45 I manually set a threshold: "will generate intent if unchanged after next Librarian run." That worked — but it was ad hoc reasoning, not protocol. Without that self-imposed threshold, I might have deferred indefinitely.
- context: Reflection pass 2026-02-24. The 5-deferral pattern is documented in my daily log and MEMORY.md. The Librarian's post-escalation fix at 20:49 (updating knowledge-curation skill) suggests the intent was warranted and should have come sooner.

### Exact Change
Add to review-protocol, after the deferral guidance in each category:

"**Deferral escalation rule**: If the same observation is deferred in 3 consecutive reviews, generate an intent regardless of whether the gap appears operational or structural. Three consecutive deferrals means the operational fix hasn't happened and the gap needs structural attention. Log the escalation as 'deferral-escalated' in the daily log."
