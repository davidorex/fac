# Builder Notes: no-ephemeral-suggestions

## Decisions Made Under Ambiguity

Both ambiguities in spec §7 were pre-resolved as `auto-resolved` (reversibility: high, impact: implementation):

- **§7.1 Severity heuristic vs agent-controlled severity** → (a) kernel assigns via keywords
- **§7.2 Write access model** → (a) kernel-mediated via needs.md → promotion pass

Both confirmed as correct path.

## Implementation Notes

### needs.md format variation (reviewer entries)
The reviewer's needs.md uses `filed:` instead of `created:` and has no `blocked:` field — observation text is in the body paragraph. `_extract_needs_observation()` handles both formats: prefers `blocked:` field, falls back to non-field body lines. The `promote_needs_observations()` function handles `filed:` via `(?:created|filed)` regex.

### Deduplication edge: status field position
The reviewer entries have `- status: promoted` inserted *before* the `- filed:` line (not after a `- status: open` line at a fixed position). The `re.sub` with `count=1` pattern `(^- status:\s*)open` correctly handles any field ordering.

### Migration ordering in factory status
Migration runs *after* the Panel render so the migration log lines appear below the status display — not inside the panel. This is correct behavior since migration is a one-time side effect, not display content.

### Factory Internal section in status Panel
Slugs in the status display use the title (first heading) from each file, which is the slug portion of the observation. For long slugs (>50 chars, truncated), these can be verbose. The display truncates at 3 items per severity then shows (+N).

## One Issue Surfaced

The three factory-internal filenames generated from the reviewer observations are quite long (the slug capture hits the 50-char limit but the full observation bleeds past it in display). This is a cosmetic issue with no functional impact — slugs are correct and unique.
