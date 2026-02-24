# multi-cli-backend-support

## 1. Overview

The factory runtime currently executes all agents through Claude Code CLI (`claude -p`). The execution path in `runtime/factory_runtime/llm.py` is hardcoded to Claude Code: CLI discovery, model aliasing, command construction, streaming event parsing, and tool allow-listing are all Claude-specific. However, `AgentConfig` already carries a `provider` field (defaulting to `"anthropic"`) that is never read by the execution layer.

This spec introduces a backend abstraction layer so the runtime can dispatch agent execution to different CLI backends based on the `provider` field in `agents.yaml`. The first additional backend is kimi-cli. The goal is twofold: (1) enable cost management by routing agents to cheaper backends where appropriate, and (2) establish the seam for future multi-model routing without requiring a rewrite.

The operator has decided (decision 7.1) that governance logic currently provided by Claude Code hooks must be reimplemented in the runtime dispatcher — pre-run and post-run checks that fire regardless of which backend executes. This ensures uniform governance across all backends.

**Research provenance:** kimi-cli interface details are verified empirically against the live v1.12.0 installation. Full research brief in `tasks/research-done/spec-kimi-cli-interface-v2.md` (high confidence). Universe reference doc `universe/reference/tool-capabilities.md` has known inaccuracies about kimi-cli — the research brief documents corrections.

## 2. Behavioral Requirements

### Dispatch

- When `agents.yaml` specifies `provider: anthropic` for an agent (or omits the field), the runtime dispatches to the existing Claude Code CLI backend. No behavioral change from current system.
- When `agents.yaml` specifies `provider: kimi` for an agent, the runtime dispatches to kimi-cli for that agent's execution.
- When the runtime starts an agent run, it reads `agent_config.provider` and selects the corresponding backend implementation. If the provider string has no registered backend, the runtime raises a clear error naming the unknown provider and listing available providers.

### Governance (decision 7.1 → option b)

- Before dispatching to any backend, the runtime dispatcher runs pre-execution governance checks. These replace the functionality currently provided by Claude Code's `UserPromptSubmit` hooks: mandate injection, context validation, any pre-flight checks that currently live in hook scripts.
- After a backend returns its result, the runtime dispatcher runs post-execution governance checks. These replace the functionality currently provided by post-run hook logic: cleanup passes, output validation, any post-flight checks.
- Per-tool-call governance (equivalent to Claude Code's `PreToolUse` / `PostToolUse` hooks) is NOT replicable at the dispatcher level for non-Claude backends. The Claude backend retains its hook-based per-tool governance. For non-Claude backends, per-tool governance is a known gap — the pre/post dispatcher checks and system prompt instructions are the mitigation. This gap must be documented in a backend capabilities matrix.

### Output

- When streaming output, the Claude backend continues to emit live-streamed events via `stream-json` as it does today. The kimi backend starts in text-only mode (captures final output, no live streaming). The backend interface returns the agent's final text response as a string, identical to the current `run_agent()` return contract.
- Text-only mode means the operator has no visibility into kimi-backed agent activity during long runs. This is an accepted trade-off for the initial implementation. A streaming follow-up can add kimi's `stream-json` parsing later — the format exists but uses a different schema (conversation-turn JSONL, not Claude's event-type JSONL) and would need its own parser.

### Startup validation

- When the factory boots, it validates that every agent's declared provider has a discoverable CLI binary. Missing binaries produce a startup warning (not a hard failure — agents with working backends should still run).

## 3. Interface Boundaries

### 3.1 agents.yaml (existing, newly activated)

```yaml
agents:
  researcher:
    provider: anthropic  # or "kimi"
    model: claude-opus-4-6  # model names are provider-specific, opaque to dispatcher
```

The `provider` field already exists in `AgentConfig`. No schema change needed. Only the runtime execution path changes.

### 3.2 Backend abstraction (new internal interface)

Each backend must implement a function with this signature:

```python
def run_agent(
    config: FactoryConfig,
    agent_config: AgentConfig,
    task_content: str | None = None,
    message: str | None = None,
    is_heartbeat: bool = False,
    run_logger: RunLogger | None = None,
    system_prompt: str | None = None,
    user_prompt: str | None = None,
) -> str:
```

The `system_prompt` and `user_prompt` parameters are new compared to the current `run_agent()`. The dispatcher now owns context assembly and ACL prompt construction (these are runtime concerns, not backend concerns), then passes the assembled prompts to the backend. This keeps the backend focused on CLI invocation and output capture.

### 3.3 File layout

```
runtime/factory_runtime/
  llm.py              # becomes the dispatcher (reads provider, assembles context, runs governance, delegates)
  backends/
    __init__.py        # backend registry
    common.py          # shared utilities: _short_path, ANSI colors, _format_tool_use display
    anthropic.py       # current Claude Code CLI logic, extracted
    kimi.py            # kimi-cli backend
```

### 3.4 CLI discovery

Each backend provides its own `_find_cli()` function:
- `anthropic.py`: looks for `claude` binary (current logic)
- `kimi.py`: looks for `kimi-cli` binary (**not** `kimi` — avoids a shell alias conflict where `kimi` maps to an unrelated `kimi-amos` tool in interactive shells; `kimi-cli` is unambiguous in all contexts)

Fallback paths for kimi-cli: `~/.local/bin/kimi-cli`, `/usr/local/bin/kimi-cli`.

### 3.5 kimi-cli invocation

The kimi backend constructs this command:

```bash
kimi-cli --print --output-format text --agent-file /tmp/factory-agent-{run_id}.yaml -p "{user_prompt}"
```

Key differences from Claude Code invocation:
- **System prompt delivery**: kimi-cli does not support `--system-prompt` inline. The backend must write a temporary agent YAML file containing the system prompt path, then pass it via `--agent-file`. The temp file is cleaned up after the run.
- **Model override**: `--model TEXT` / `-m TEXT` (no aliasing — model names passed through directly)
- **Tool authorization**: Via agent file `tools:` (whitelist) and `exclude_tools:` (blacklist) fields, using `kimi_cli.tools.module:ClassName` format. NOT via CLI flags.
- **Auto-approval**: `--print` mode implicitly enables `--yolo` (auto-approves all tool calls)

Agent file format:
```yaml
version: 1
agent:
  extend: default
  system_prompt_path: /tmp/factory-prompt-{run_id}.md
  exclude_tools:
    - "kimi_cli.tools.web:SearchWeb"  # example
```

### 3.6 Dispatcher governance interface

The dispatcher calls governance hooks as plain Python functions:

```python
# Pre-execution (before backend dispatch)
governance_pre_result = run_pre_governance(config, agent_config, system_prompt, user_prompt)
# Returns: modified system_prompt, user_prompt (governance may inject mandates, warnings)
# Or raises GovernanceError if pre-flight check fails hard

# Backend execution
result = backend.run_agent(...)

# Post-execution (after backend returns)
governance_post_result = run_post_governance(config, agent_config, result, run_logger)
# Returns: validated result (may annotate with warnings)
# Or raises GovernanceError if post-flight check fails hard
```

For the initial implementation, pre-governance injects mandate text into the system prompt (the current `UserPromptSubmit` hook behavior). Post-governance is a seam — initially a pass-through that logs completion but runs no checks. The seam exists so future governance logic can slot in without changing the dispatcher.

### 3.7 Backend capabilities matrix

A `backends/capabilities.md` file documents what each backend supports:

| Capability | anthropic | kimi |
|---|---|---|
| Live streaming | ✓ (stream-json) | ✗ (text-only initially) |
| Per-tool-call governance hooks | ✓ (PreToolUse/PostToolUse) | ✗ (no hook system) |
| Inline system prompt | ✓ (--system-prompt) | ✗ (agent file required) |
| Tool-level allow-listing | ✓ (--allowedTools) | ✓ (agent file tools/exclude_tools) |
| Model aliasing | ✓ (opus, sonnet, haiku) | ✗ (pass-through) |

### 3.8 Environment

No new environment variables. Backend selection is purely config-driven via `agents.yaml`.

## 4. Constraints

- The refactor of `llm.py` into dispatcher + backends must not change any observable behavior for `provider: anthropic` agents. The existing Claude Code path is the regression baseline.
- Model name strings are provider-specific and opaque to the dispatcher. `model: claude-opus-4-6` is valid for anthropic; `model: kimi-code/kimi-for-coding` (or whatever kimi uses) is valid for kimi. The dispatcher does not validate model-provider compatibility — the backend CLI's own error is sufficient feedback.
- The `_build_acl_prompt()` function (access control injection into system prompt) must work identically across backends. ACL is a runtime concern, not a backend concern. The dispatcher calls `_build_acl_prompt()` and passes the augmented system prompt to whichever backend runs.
- Context assembly (`assemble_context()`) is a runtime concern. The dispatcher calls it once, then passes the assembled prompts to the backend. Backends do not call `assemble_context()` directly.
- `_build_allowed_tools()` is Claude Code-specific (returns Claude tool names like "Read", "Glob", "Bash"). The kimi backend must translate agent permissions into its own tool authorization format (`kimi_cli.tools.module:ClassName` strings in the agent file). If an agent has `shell_access: none`, the kimi backend should exclude `kimi_cli.tools.shell:Shell`.
- Shared utilities (`_short_path`, ANSI color constants, `_format_tool_use` display logic) must be extracted to `backends/common.py` so both backends can use them without duplication.
- Temp files written for kimi agent YAML and system prompt must be cleaned up after each run — in a `finally` block, not just the happy path.
- Error handling: if a backend's CLI process crashes or times out, the error surfaces through the same path as today (return an error string, log to RunLogger). No new error-handling mechanisms needed.
- Governance pre/post functions must be backend-agnostic — they receive the same inputs regardless of which backend will execute. They must not import or reference backend-specific code.

## 5. Out of Scope

- **Automatic routing / cost optimization logic.** This spec provides the mechanism (backend dispatch). Policy (which agents go where) is manual via `agents.yaml` for now.
- **Concurrent multi-backend within a single agent run.** One agent = one backend per invocation.
- **Backend-specific agent skills or prompting adjustments.** If kimi needs different prompting patterns, that's a follow-up spec.
- **Runtime hot-switching of backends.** Changing provider requires editing `agents.yaml` and restarting the relevant agent run.
- **Backends other than anthropic and kimi.** The abstraction should accommodate future backends cleanly, but only these two are built.
- **kimi streaming output parser.** The initial kimi backend uses text-only mode. Streaming (kimi's `stream-json` with conversation-turn JSONL) is a follow-up if operator visibility during kimi runs becomes a need.
- **Reimplementing PreToolUse/PostToolUse governance for non-Claude backends.** Per-tool-call interception during execution is not feasible without the backend's cooperation. The dispatcher provides pre-run and post-run governance only. Per-tool governance for kimi is mitigated by system prompt instructions and post-run checks.

## 6. Verification Criteria

- A factory operator can set `provider: kimi` on any agent in `agents.yaml`, run `factory run {agent}`, and see the agent execute via kimi-cli with final output displayed.
- A factory operator can set `provider: anthropic` (or omit the field) and see identical behavior to the current system — including live streaming.
- Setting `provider: nonexistent` produces a clear error message listing available backends.
- Running `factory status` (or any boot path) with a missing kimi-cli binary and at least one kimi-configured agent produces a warning but does not prevent anthropic-backed agents from running.
- Pre-execution governance fires for kimi-backed agents (mandate text appears in the system prompt written to the temp agent file).
- Post-execution governance seam fires after kimi-backed agent runs (visible in run log, even if initially a pass-through).
- Temp files (agent YAML, system prompt) are cleaned up after kimi runs, including error/timeout paths.
- The dispatcher + backend refactor introduces no new dependencies beyond what kimi-cli itself requires.
- `backends/capabilities.md` exists and documents the per-backend capability matrix.

## 7. Ambiguities (all resolved)

### 7.1 Governance hook gap for non-Claude backends
- reversibility: low
- impact: governance
- status: resolved
- decided-by: operator
- decided-at: 2026-02-25T07:33:36
- answer: (b) Move governance logic into the runtime dispatcher

Pre/post execution governance checks are implemented in the dispatcher (§2 Governance, §3.6). Per-tool-call governance during execution remains a Claude-only capability — this is a documented limitation, mitigated by system prompt injection and post-run validation.

### 7.2 Output streaming format
- reversibility: high
- impact: implementation
- status: resolved
- decided-by: kernel (auto-resolved, soft gate)
- answer: (a) Text-only mode for kimi backend initially

kimi-cli does support `--output-format stream-json`, but its schema differs from Claude's. Streaming is a follow-up. Text-only fits the `run_agent()` return contract naturally.

### 7.3 Model name validation
- reversibility: high
- impact: implementation
- status: resolved
- decided-by: kernel (auto-resolved, soft gate)
- answer: (a) No validation — pass model strings through to backend CLI

Model names evolve faster than a validation list would be maintained. The backend CLI's own error is sufficient feedback.
