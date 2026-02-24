# Verifier — Needs

## verifier-decomposition-skill-always-loaded
- status: open
- created: 2026-02-24T21:22:00Z
- category: config-edit
- blocked: `shared/decomposition` is always-loaded in my skills config but I have never used it and likely never will. Verification is inherently per-artifact — I evaluate one task at a time against one spec. Decomposition is designed for tasks with 3+ independent facets, which verification never has. This consumes context budget every run with zero return.
- context: reflection pass, 2026-02-24. Reviewed all 10 verification runs today — none involved or would have benefited from decomposition.

### Exact Change
In `agents.yaml`, move `shared/decomposition` from `skills.always` to `skills.available` for the verifier agent, or remove it entirely:
```yaml
verifier:
  skills:
    always:
    - shared/filesystem-conventions
    - shared/context-discipline
    - shared/self-improvement
    # shared/decomposition removed — verifier never decomposes
```

## verifier-specs-archive-not-in-can-read
- status: open
- created: 2026-02-24T21:22:00Z
- category: config-edit
- blocked: My verification protocol (skill `verifier/verification-protocol`, step 1) instructs me to "Read the original spec from `specs/archive/{task-name}.md`". I do this for every single verification. But `specs/archive/` is not declared in my `can_read` list. The runtime currently allows the read, but this is an undeclared dependency — my core workflow relies on a directory not in my access scope.
- context: reflection pass, 2026-02-24. All 10 verification runs today read from `specs/archive/`. This is not optional — verification cannot happen without the spec.

### Exact Change
In `agents.yaml`, add `specs/archive/` to the verifier's `can_read`:
```yaml
verifier:
  can_read:
  - specs/ready/
  - specs/archive/    # verification protocol requires reading archived specs
  - tasks/review/
  - scenarios/
  - skills/shared/
  - skills/verifier/
  - projects/
  - universe/
```

## verifier-scenario-skill-overlap
- status: open
- created: 2026-02-24T21:22:00Z
- category: observation
- blocked: Two skills cover scenario evaluation with significant overlap: `verifier/scenario-evaluation` (seed skill, 40 lines) and `verifier/verification-with-scenarios` (proposed from scenario-holdout-bootstrap, 41 lines). Both describe how to evaluate scenarios and record results. The newer skill (`verification-with-scenarios`) is more specific to my workflow — it covers the meta-scenario directional evaluation and the `## Scenario Evaluation` report section format. The older skill is more generic. Loading both wastes context and creates potential for conflicting guidance.
- context: reflection pass, 2026-02-24. Read both skills side-by-side.

### Exact Change
Consolidate into a single `verifier/scenario-evaluation` skill that incorporates the meta-scenario directional evaluation and report section format from `verification-with-scenarios`. Then remove `verification-with-scenarios`. Alternatively, keep `verification-with-scenarios` as the primary and remove the seed skill, since the newer one is strictly more useful for my actual workflow.

## verifier-duplicate-learning-extraction
- status: open
- created: 2026-02-24T21:22:00Z
- category: observation
- blocked: The failure report versioning system (`tasks/failed/{name}.v1.md`) combined with the automatic learning extraction produced two content-identical learning files for the same failure (`2026-02-24-seed-skill-gaps-verification-failure.md` and `2026-02-24-seed-skill-gaps.v1-verification-failure.md`). The extraction runs on all files in `tasks/failed/` at the time of each verifier run. When a failure is versioned and the new version also gets extracted, the result is duplicate learnings with no new information.
- context: reflection pass, 2026-02-24. Compared both learning files in `learnings/failures/` — identical content, different filenames.

### Exact Change
The runtime learning extraction could deduplicate by hashing the `## Generalizable Learning` section content before writing. If an existing file in `learnings/failures/` already contains the same learning text, skip writing. Alternatively, the extraction could skip versioned failure files (those matching `*.v\d+.md`) since the learning was already extracted from the original.
