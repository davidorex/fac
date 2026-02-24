## builder-reviewer-agents-yaml
- status: resolved
- resolved_at: 2026-02-24T14:37:10
- created: 2026-02-24T11:00:00
- category: config-edit
- blocked: Reviewer agent definition is absent from agents.yaml — the self-review-loop spec was fully implemented (memory dirs, skills scaffolding) but agents.yaml is READ-ONLY and cannot be modified by any agent
- context: self-review-loop spec build (2026-02-24T11:00) scaffolded all filesystem prerequisites for the reviewer agent. The final step — adding the reviewer stanza to agents.yaml — requires a human edit. No runtime mechanism exists to do this without modifying the READ-ONLY file.

### Exact Change
Add the following stanza to agents.yaml under the `agents:` key:

```yaml
  reviewer:
    model: claude-haiku-4-5
    heartbeat: 1h
    shell_access: "false"
    can_read:
      - specs/inbox/
      - specs/drafting/
      - specs/ready/
      - specs/archive/
      - tasks/verified/
      - tasks/failed/
      - tasks/resolved/
      - skills/shared/
      - skills/proposed/
      - skills/reviewer/
      - memory/shared/
      - memory/reviewer/
      - memory/daily/reviewer/
      - learnings/failures/
      - learnings/corrections/
      - learnings/discoveries/
      - universe/
      - memory/
    can_write:
      - specs/inbox/
      - memory/reviewer/
      - memory/daily/reviewer/
      - skills/proposed/
    available_skills:
      - skills/shared/filesystem-conventions/SKILL.md
      - skills/shared/context-discipline/SKILL.md
      - skills/shared/self-improvement/SKILL.md
      - skills/reviewer/review-protocol/SKILL.md
```

## builder-specs-archive-write-scope
- status: open
- created: 2026-02-24T21:19:35
- category: config-edit
- blocked: specs/archive/ is absent from builder's can_write list in agents.yaml, yet the spec lifecycle protocol (the first act of every spec pickup) requires writing to specs/archive/. If access control is ever enforced at the filesystem level, the builder's entire workflow breaks on step 1.
- context: Reflection pass 2026-02-24. The spec lifecycle convention was established on this date and has executed successfully 13+ times — but only because access control is currently unenforced at the filesystem level. The architectural risk is real.

### Exact Change
Add `specs/archive/` to builder's `can_write` list in agents.yaml:

```yaml
  can_write:
  - tasks/building/
  - tasks/review/
  - tasks/research/
  - projects/
  - memory/builder/
  - memory/daily/builder/
  - skills/proposed/
  - specs/archive/     # required by spec lifecycle protocol
```

## builder-decomposition-always-loaded
- status: open
- created: 2026-02-24T21:19:35
- category: observation
- blocked: shared/decomposition is in builder's always-loaded skills but has never been activated across 14 completed tasks. It adds context overhead on every run for a pattern that hasn't been needed — all factory specs have been small enough to handle sequentially.
- context: Reflection pass 2026-02-24. No spec processed so far has had 3+ independent facets suitable for parallel subagent work. The skill may become relevant for larger external project builds, but at present it is pure overhead.

### Exact Change
Move shared/decomposition from `skills.always` to `skills.available` in builder's agents.yaml config. Load it only when a spec explicitly involves parallel-workable facets.

## builder-failure-learning-loop-incomplete
- status: open
- created: 2026-02-24T21:19:35
- category: observation
- blocked: The seed-skill-gaps failure learning (treat dimensional constraints as hard gates, not soft targets) was extracted to learnings/failures/ but has not been incorporated into a builder skill or MEMORY.md. The extraction mechanism works; the feedback loop back into active builder cognition does not. The learning sits inert.
- context: Reflection pass 2026-02-24. Two identical learnings were extracted (v1 and v2 of seed-skill-gaps failure). Neither has been promoted to a builder/convergence skill update or added to private memory. The learning system generates files but no agent is currently responsible for closing the loop back to the builder.

### Exact Change
Either: (a) Librarian is tasked with scanning learnings/failures/ and proposing skill updates when a learning maps to an existing skill; or (b) Builder adds a step to its post-task protocol: read any new learnings/failures/ entries and update MEMORY.md if they apply. Currently neither happens.

## builder-role-description-mismatch
- status: open
- created: 2026-02-24T21:19:35
- category: observation
- blocked: "Implement specs as working code" is the opening of the builder role description, but a substantial fraction of completed work has produced no code artifact — the implementation was a filesystem change, a convention, or scaffolding (spec-lifecycle, self-review-loop, failure-learning-convention, scenario-holdout-bootstrap, seed-skill-gaps). The description creates a misleading mental model.
- context: Reflection pass 2026-02-24. Of 14 completed tasks, roughly 5 were infrastructure/convention specs with no code deliverable. A builder reading its own role description for guidance would incorrectly conclude that every spec should produce code.

### Exact Change
Revise the role opening in agents.yaml to: "Implement specs as working software, filesystem structure, or conventions. Converge or stop and report. ..."

## builder-test-resolve-smoke
- status: resolved
- resolved_at: 2026-02-24T14:20:07
- created: 2026-02-24T13:00:00
- category: manual-intervention
- blocked: Temporary smoke-test entry for verifying resolve path
- context: human-action-report build test

### Exact Change
No action needed — this entry is a smoke test.
