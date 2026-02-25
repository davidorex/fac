# Verification Report: multi-cli-backend-support

spec: specs/archive/multi-cli-backend-support.md
reviewed_at: 2026-02-25T08:03:39
verdict: SATISFIED (9/10)

## Summary

Backend dispatch abstraction implemented as specified. `llm.py` refactored from monolithic Claude Code CLI invoker into a clean dispatcher that owns context assembly, ACL injection, and governance pre/post hooks. Two backends registered: `anthropic` (extracted existing Claude Code CLI logic) and `kimi` (new kimi-cli backend). All nine verification criteria from the spec are addressed.

## Criterion-by-Criterion Assessment

### 1. `provider: kimi` → kimi-cli dispatch
**Satisfied.** `backends/kimi.py` implements `run_agent()` with the correct kimi-cli invocation: `--print --output-format text --agent-file` and `-p` for user prompt. Agent YAML written to `/tmp/factory-agent-{uuid8}.yaml` with `system_prompt_path` reference. Binary discovery uses `kimi-cli` (not `kimi`), with fallback paths.

### 2. `provider: anthropic` → identical live streaming
**Satisfied.** `backends/anthropic.py` preserves the exact execution path from the original `llm.py`: same command construction (`-p`, `--model`, `--system-prompt`, `--output-format stream-json`, `--verbose`, `--no-session-persistence`, `--permission-mode bypassPermissions`), same stream-json event parsing, same stderr thread handling. The only observable change: the run header now prints `(model, provider: anthropic)`.

### 3. Unknown provider → clear error
**Satisfied.** `get_backend()` in `backends/__init__.py` raises `ValueError` with: `"Unknown provider '{provider}'. Available backends: anthropic, kimi"`.

### 4. Missing kimi-cli → startup warning, anthropic unaffected
**Satisfied.** `validate_providers()` in the dispatcher iterates unique providers, calls `backend._find_cli()`, catches `FileNotFoundError` → produces a warning string. Missing binaries do not block other agents.

### 5. Mandate text in kimi system prompt
**Satisfied.** `run_pre_governance()` loads mandates from `~/.claude/mandates.jsonl` and `{workspace}/.claude/mandates.jsonl`, formats them, and appends to `system_prompt` before backend dispatch. The kimi backend writes this augmented system prompt to the temp file at `prompt_path`. The pre-governance is backend-agnostic as specified.

### 6. Post-governance event logged
**Satisfied.** `run_post_governance()` logs a `governance_post` event via `run_logger.log_event()` with provider, result length, and NO_REPLY detection. Currently a pass-through seam — correct per spec §3.6.

### 7. Temp file cleanup in finally block
**Satisfied.** `kimi.py` lines 180-187: `finally` block iterates `[prompt_path, agent_file_path]`, calls `path.unlink()` with exception suppression. Covers happy path, `TimeoutExpired`, and general `Exception` paths.

### 8. No new pip dependencies
**Satisfied.** New code uses only `yaml` (already used by `config.py`, `context.py`, `cli.py`, `run_log.py`), `uuid`, `subprocess`, `shutil`, `json`, `threading`, `pathlib` — all stdlib or already present.

### 9. capabilities.md
**Satisfied.** `backends/capabilities.md` documents the 9-row capability matrix, the per-tool-call governance gap with mitigations, the operator visibility gap, and binary discovery paths. Matches spec §3.7.

## Structural Verification

- **Interface compliance:** Backend `run_agent()` signatures match spec §3.2 exactly (`config`, `agent_config`, `task_content`, `message`, `is_heartbeat`, `run_logger`, `system_prompt`, `user_prompt` → `str`).
- **Dispatcher public API preserved:** All four callers in `cli.py` import `run_agent` and `validate_providers` from `llm.py` — both present with compatible signatures. No callers depended on removed internal functions.
- **Backend registry imports cleanly:** Verified `get_backend('anthropic')` and `get_backend('kimi')` resolve without import errors.
- **Context assembly ownership correct:** Dispatcher calls `assemble_context()` once, passes assembled prompts to backend. Backends do not call `assemble_context()`.
- **ACL injection ownership correct:** `_build_acl_prompt()` is in the dispatcher, not in backends. Same text injected regardless of backend.
- **Governance is backend-agnostic:** `run_pre_governance()` and `run_post_governance()` do not import or reference backend-specific code.

## Minor Observation (non-blocking)

`anthropic.py` line 68: `message = event.get("message", {})` is assigned but unused — line 69 re-fetches from `event` directly. This existed in the original code and is cosmetic. Not a functional issue.

## Satisfaction Score: 9/10

The implementation satisfies all verification criteria with clean architecture. The 1-point deduction reflects that the anthropic backend extraction, while behaviorally identical, carries the minor dead-variable cosmetic issue from the original code — and the spec's mention of "no behavioral change" is honored only to the extent that the original behavior was correct (which it was). A score of 10 would require zero code-quality observations of any kind.

**Score reasoning (not 10, not 8):** All nine criteria met, all structural constraints satisfied, governance seams correctly placed, cleanup paths verified. The implementation goes beyond minimum compliance — the capabilities.md is thorough, the docstrings document architectural rationale, and the builder notes call out deliberate design decisions. This is above the 8/10 pass threshold with confidence.

## Meta-Scenario Alignment

This change moves the factory **closer** to the meta-scenario. Multi-backend dispatch increases pipeline autonomy: the operator can now route agents to cheaper/specialized backends without pipeline changes. The governance abstraction ensures uniform mandate coverage across backends — reducing the risk that backend diversification weakens governance. The accepted gaps (per-tool-call governance for kimi, no streaming) are documented with mitigations and follow-up paths.
