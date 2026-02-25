# Outcome

**no-ephemeral-suggestions** is now in `specs/ready/`, unblocked for Builder.

**What the spec covers:**

- **New directory** `specs/factory-internal/` — every observation becomes a dated, severity-tagged file (`2026-02-25T0817-low-decisions-gc-gap.md`)
- **Kernel-mediated writes** — agents keep writing to `needs.md` (no agents.yaml changes needed), kernel promotes to factory-internal in the post-run pass. Safety-net extraction writes directly to factory-internal instead of needs.md.
- **Severity heuristics** — kernel classifies as `critical`/`high`/`low` via keyword matching. Operator can reclassify.
- **`factory triage` command** — `--list`, `--promote` (→ `specs/inbox/`), `--dismiss --reason "..."`. Slug or full filename addressing.
- **`factory status` integration** — "Factory Internal" section with severity-grouped counts
- **`factory needs` cleanup** — observations removed from needs output (they're now in triage)
- **One-time migration** of existing needs.md observation entries (NEED-R001/R002/R003)
- **GC pass** — `cleanup-factory-internal` removes promoted+archived and old dismissed files

Two ambiguities identified, both auto-resolved as soft gates (severity assignment and write access model).
