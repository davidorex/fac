# Outcome

**multi-cli-backend-support** has been promoted from `specs/drafting/` to `specs/ready/`.

**What changed since last session:**
- Incorporated operator decision 7.1 → **(b)**: governance logic moves into the runtime dispatcher as pre/post execution checks. Added §2 Governance section, §3.6 dispatcher governance interface, and the per-tool-call gap as a documented limitation.
- Incorporated verified research findings: corrected binary name to `kimi-cli`, added full kimi invocation details (§3.5), agent file format, tool authorization mapping, capabilities matrix (§3.7).
- Refactored the backend interface (§3.2) — dispatcher now owns context assembly and passes `system_prompt`/`user_prompt` to backends, keeping backends focused on CLI invocation.
- Added 4 new verification criteria (governance firing, temp cleanup, capabilities matrix).
- All 3 ambiguities marked resolved in §7 with decisions, rationale, and cross-references to spec sections.

**Pipeline state:** `specs/ready/multi-cli-backend-support.md` is now available for Builder pickup. The research brief at `tasks/research-done/spec-kimi-cli-interface-v2.md` accompanies it with the full verified kimi-cli tool inventory and invocation details.
