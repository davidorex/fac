# Builder — Needs & Observations

## builder-empty-private-memory
- status: open
- created: 2026-02-25T20:52:31
- category: observation
- blocked: Private MEMORY.md has zero entries after completing 3+ tasks (hello-world-python, multi-cli-backend-support, no-ephemeral-suggestions). Each new builder session starts cold with no curated knowledge. Builder-specific patterns, factory conventions discovered during implementation, and tool quirks (e.g., the `rm` interactive alias) are not being preserved in the builder's own memory — they exist only in shared KNOWLEDGE.md or git history.
- context: Reflection pass 2026-02-25. Pattern identified: MEMORY.md has never been written to.

### Exact Change
After each task completion, builder should write builder-specific durable knowledge to MEMORY.md: implementation patterns encountered, spec format nuances, factory conventions that surprised me, tool behaviors. The existing shared/self-improvement skill covers learnings/ but not private MEMORY.md curation. Consider whether implementation-approach skill should include a MEMORY.md write step as part of task completion.

---

## builder-no-daily-logs
- status: open
- created: 2026-02-25T20:52:31
- category: observation
- blocked: memory/daily/builder/ contains no log files. The context-discipline skill specifies writing checkpoint logs during long tasks and summaries when finishing tasks. After 3 completed tasks, there is no logged session history. When context degrades mid-task or sessions need to resume, there is no prior-state record to recover from.
- context: Reflection pass 2026-02-25. Directory exists, no files written.

### Exact Change
Builder should write a daily log entry at task completion — at minimum a one-paragraph summary of what was built, decisions made, and any concerns. The implementation-approach skill (step 8) specifies builder-notes.md for the verifier; the daily log is the builder's own continuity record. These are different artifacts serving different readers.

---

## builder-notes-path-inconsistency
- status: open
- created: 2026-02-25T20:52:31
- category: observation
- blocked: Two authoritative sources specify conflicting paths for builder-notes files. The `builder/implementation-approach` skill (step 8) says: `tasks/review/{task}/builder-notes.md` (subdirectory per task). The filesystem-conventions KNOWLEDGE.md entry says: `tasks/review/{task-name}.builder-notes.md` (flat file at review/ root). These are structurally different. A builder following the skill would write to a subdirectory; a builder following the naming convention would write a flat file. The verifier will look in one location; the builder may write to the other.
- context: Reflection pass 2026-02-25. Found during cross-referencing implementation-approach skill against filesystem-conventions.

### Exact Change
Align on one canonical path. Recommend the flat-file convention (`tasks/review/{task-name}.builder-notes.md`) since it matches the naming scheme for all other task files in that directory (they are all flat named files, not subdirectories). Update `implementation-approach` skill step 8 to use the flat path. If subdirectory structure is intended, document why and update KNOWLEDGE.md accordingly.

---

## builder-core-skills-available-not-always
- status: open
- created: 2026-02-25T20:52:31
- category: observation
- blocked: `builder/implementation-approach` and `builder/convergence` are in the `available` skill list (loaded on demand), not `always`. These are the two skills most central to my job function — one defines the build sequence, the other defines when to stop. Across 3 completed tasks, I have been building without explicitly loading these skills (no record of activation). Context-discipline reasoning for keeping always-loaded list small is valid. But if these skills are not being loaded per-task, I may be implicitly following their guidance from prior context rather than explicitly from skill content — which degrades as context fills.
- context: Reflection pass 2026-02-25. Skills list audit.

### Exact Change
Two options: (1) Move implementation-approach and convergence to `always` — accepted context cost for correctness guarantee. (2) Keep as available but add an explicit step to the builder's startup protocol (in role description or MEMORY.md) to load them at task start before reading the spec. Option 2 preserves context budget discipline while closing the gap. The human decides which trade-off is acceptable.
