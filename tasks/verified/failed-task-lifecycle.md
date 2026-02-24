# Verification Report: failed-task-lifecycle

spec: specs/archive/failed-task-lifecycle.md
reviewed_at: 2026-02-24T13:55
verdict: SATISFIED (9/10)

## Summary

All spec criteria satisfied. The `tasks/resolved/` directory exists and is correctly integrated into `factory init`, `factory status`, and the post-execution hook sequence. Automatic resolution (`resolve_completed_failures`) correctly moves versioned and active failure reports from `tasks/failed/` to `tasks/resolved/` with `## Resolution` annotations. Manual resolution (`factory resolve`) works correctly with required `--reason` flag, git commit, and proper error handling. Evidence: `seed-skill-gaps.v1.md` resolved by rebuild with correct annotation, `self-review-loop.md` resolved manually with reason. `tasks/failed/` is now empty — only genuinely unresolved failures would remain.

## Verification Criteria Checklist

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `seed-skill-gaps.v1.md` moved to `tasks/resolved/` with `resolved_by: rebuild` | PASS — file exists with correct `## Resolution` section (rebuild, timestamp, verified_task reference) |
| 2 | `factory resolve self-review-loop --reason "..."` moves report with reason | PASS — file exists in `tasks/resolved/` with `resolved_by: manual`, reason text preserved |
| 3 | `factory resolve` without `--reason` errors and exits non-zero | PASS — Click `required=True` on `--reason` option (line 875) handles this |
| 4 | `factory resolve nonexistent-task --reason "test"` → exit 1 with error | PASS — `resolve_task` returns `(1, "No failure report found...")` when `active.exists()` is False |
| 5 | `factory status` shows `tasks/resolved/` with item count | PASS — added to `pipeline_dirs` list at line 692 |
| 6 | `tasks/failed/` contains only unresolved failures | PASS — currently empty (only `.gitkeep`); both resolved items moved out |
| 7 | `factory init` creates `tasks/resolved/` | PASS — present in `dirs` list at line 511 |

## Resolution Annotation Verification

**seed-skill-gaps.v1.md** (automatic):
```
## Resolution
- resolved_by: rebuild
- resolved_at: 2026-02-24T13:52:39
- verified_task: tasks/verified/seed-skill-gaps.md
```
Matches spec format. Annotation appended to end of existing content without modifying prior sections.

**self-review-loop.md** (manual):
```
## Resolution
- resolved_by: manual
- resolved_at: 2026-02-24T13:52:47
- reason: human added reviewer agent to agents.yaml
```
Matches spec format. Reason text preserved verbatim.

## Hook Ordering

Post-execution sequence (lines 599-619):
1. Spec pipeline cleanup (every agent) ✓
2. Task review cleanup (every agent) ✓
3. Failure resolution (verifier only) ✓
4. Failure learning extraction (verifier only) ✓

Resolution fires only after verifier execution (`if agent == "verifier"` at line 609), preventing premature resolution — matches spec constraint.

## Satisfaction Score: 9/10

Implementation is complete and correct across all spec requirements. The resolution annotations are well-formatted, error paths are properly handled, git integration works, and the hook ordering is exactly as specified. Both resolution paths (automatic rebuild + manual) are demonstrated by real resolved files in the workspace. Minor note: the `show_workspace` command (line 762) does not include `tasks/resolved` in its sections list — but this was not required by the spec (only `factory status` was specified).
