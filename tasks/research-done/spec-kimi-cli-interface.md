# Research Brief: kimi-cli Interface & Capabilities

**Requested by:** spec
**Researched by:** researcher
**Date:** 2026-02-24
**Blocks:** specs/drafting/multi-cli-backend-support.md

---

## Executive Summary

kimi-cli v1.12.0 is installed and functional on this system. It has native tool execution (file I/O, shell, web, subagents) — nearly identical to Claude Code's tool suite. This means multi-backend support is **Option A: a backend abstraction layer**, not a fundamental architecture change. The runtime changes are small: different flags for system prompt delivery and user message passing.

However, the universe reference doc (`universe/synthesis/kimi-cli-integration.md` and `universe/reference/tool-capabilities.md`) contain several inaccuracies verified against the live CLI. This brief documents what was verified empirically.

---

## Answers to Specific Questions

### 1. CLI Invocation Pattern

**Verified invocation equivalent to `claude -p --system-prompt "..." --output-format text`:**

```bash
kimi-cli --print --final-message-only \
  --agent-file agent.yaml \
  --prompt "user message here" \
  --yolo
```

Key differences from Claude Code:
- **System prompt**: Cannot be passed inline. Must be written to a markdown file referenced from a YAML agent spec. Verified working:
  ```yaml
  version: 1
  agent:
    extend: default
    system_prompt_path: ./assembled-prompt.md
  ```
- **User message**: Via `--prompt` flag (aliases: `-p`, `-c`). Not via stdin (stdin is for `--input-format stream-json` only).
- **Permission bypass**: `--yolo` (aliases: `--yes`, `-y`). Also implicit when `--print` is used.
- **Model selection**: Via `--model provider/model` (e.g., `--model kimi-code/kimi-for-coding`). NOT bare model names — requires a configured provider entry in `~/.kimi/config.toml`. Currently configured: `kimi-code/kimi-for-coding` (reports as Kimi k1.5).
- **Work directory**: Via `--work-dir` / `-w` (note: `-w` means work-dir in kimi, worktree in claude).

**Corrections to reference docs:**
- `--quiet` flag does NOT exist in v1.12.0. Passing it launches interactive mode without error. The correct equivalent is `--print --final-message-only`.
- `--output-format json` does NOT exist. Only `text` and `stream-json` are valid.

### 2. Tool Execution

**kimi-cli has native tool execution.** Verified built-in tools from CLI help and reference docs:

| Claude Code | kimi-cli | Notes |
|---|---|---|
| Read | ReadFile | Max 1000 lines/read, 2000 chars/line |
| Write | WriteFile | Requires approval (auto-approved in print/yolo) |
| Edit | StrReplaceFile | String replacement model |
| Bash | Shell | bash/zsh |
| Glob | Glob | Max 1000 results |
| Grep | Grep | Text search |
| WebSearch | SearchWeb | Requires `moonshot_search` service configured |
| WebFetch | FetchURL | Requires `moonshot_fetch` service configured |
| Task | Task | Subagent delegation |
| TodoWrite | SetTodoList | Task management |
| — | CreateSubagent | Runtime subagent definition (kimi-only, not default-enabled) |
| — | ReadMediaFile | Images/video up to 100MB (kimi-only) |
| NotebookEdit | — | Claude-only |
| MultiEdit | — | Claude-only |

**Verdict: kimi-cli is agentic, not text-in/text-out.** It executes tools autonomously in its own loop. The factory does NOT need to implement a tool-execution loop.

### 3. Streaming

**Verified.** `--output-format stream-json` produces JSONL.

Tested output for a simple prompt:
```json
{"role":"assistant","content":[{"type":"think","think":"...","encrypted":null},{"type":"text","text":"Hello"}]}
```

Event schema differences from Claude Code:
- Claude Code `stream-json` emits multiple event types: `assistant`, `result`, `system`
- kimi-cli `stream-json` emits message objects with `role` and `content` array containing typed blocks (`think`, `text`, and presumably `tool_use`/`tool_result` for tool calls)

The factory's event parser would need a backend-specific adapter if streaming is used. For `--print --final-message-only` (text mode), no parser needed — stdout is the response.

### 4. Model Identifiers

Model names follow the format `provider/model-name`, corresponding to entries in `~/.kimi/config.toml`.

Currently configured on this system:
- `kimi-code/kimi-for-coding` (default) — reports itself as Kimi k1.5

New models require a `[models."provider/model"]` + `[providers."provider"]` entry in config.toml. Bare names like `kimi-k2.5` are not recognized by `--model` flag.

The reference doc mentions K2 and K2.5 as available models, but these would need to be configured as provider entries. The exact model identifiers for K2/K2.5 are not currently in the config and would need to be looked up from Moonshot's API documentation or obtained when/if the user provisions them.

### 5. Permission Model

- `--yolo` / `--yes` / `-y`: auto-approve all tool calls
- `--print` mode: implicitly enables yolo
- `--agent-file`: reference doc says this also auto-enables yolo, but `--print` already covers this for factory use
- **No equivalent to Claude Code's granular `--permission-mode`** (bypassPermissions, plan, default)
- **No equivalent to `--allowedTools` / `--disallowedTools` flags**
- Tool restriction: done via `exclude_tools` list in agent YAML file (excludes specific tool classes by Python path, e.g., `kimi_cli.tools.web:SearchWeb`)

---

## What This Means for the Spec

### Architecture: Confirmed Option A (Backend Abstraction Layer)

The changes needed in `llm.py` are:

1. **System prompt delivery**: Write assembled prompt to temp `.md` file, generate a temp agent `.yaml` pointing to it
2. **User message passing**: Use `--prompt` flag instead of stdin pipe
3. **Invocation**: `kimi-cli --print --final-message-only --agent-file <path> --prompt <msg> --yolo -w <workspace>`
4. **Model dispatch**: Read `backend` and `model` fields from agents.yaml, dispatch to correct binary and model identifier
5. **Output parsing**: For text mode, stdout is the response (same as Claude). For streaming, need a backend-specific JSONL parser.

### What Does NOT Need to Change

- **Context assembly** (`context.py`): works as-is. The assembled prompt just gets written to a file instead of passed inline.
- **Skills**: kimi-cli discovers from `~/.claude/skills/` — cross-compatible format.
- **MCP**: Compatible config format (`~/.kimi/mcp.json`).
- **Access control**: Prompt-based rules injected into system prompt work with either backend.

### Caveats for the Spec

1. **`--quiet` does not exist in v1.12.0.** The reference doc is wrong. Use `--print --final-message-only`.
2. **`--output-format json` does not exist.** Only `text` and `stream-json`.
3. **Model names are not portable.** Claude uses simple aliases (`opus`, `sonnet`). Kimi uses `provider/model` compound identifiers that depend on config state. The factory would need a model-mapping layer or convention.
4. **No worktrees.** Parallel isolation via git worktrees is Claude-only. If the factory needs parallel kimi agents on the same repo, it would need its own worktree management (or accept sequential execution).
5. **No hooks.** PreToolUse/PostToolUse lifecycle events are Claude-only. Any factory hooks that enforce behavior (the mandate hooks, cleanup hooks) would not fire for kimi backends. This is a significant gap for factory governance.
6. **Agent swarm (100 parallel agents) is web-UI only.** Not available in CLI.

### Confidence Assessment

- **High confidence**: CLI flags, tool capabilities, agent file format, streaming schema — all verified empirically against live v1.12.0.
- **Medium confidence**: K2/K2.5 model availability — referenced in docs but not configured/tested on this system.
- **Low confidence**: `--quiet` and `--output-format json` may exist in a future version — the reference doc might be forward-looking. But for the spec, use what's verified in v1.12.0.

---

## Recommendation

Spec the abstraction layer as a thin dispatch in `llm.py` that:
1. Reads `backend:` from agents.yaml (default: `claude`)
2. Dispatches to `_invoke_claude()` or `_invoke_kimi()`
3. Each backend function handles its own temp file management, flag construction, and output parsing
4. Model names are specified per-backend in agents.yaml (no cross-backend normalization)

The hooks gap is the most architecturally significant concern. If factory governance hooks (mandate enforcement, cleanup, etc.) are critical to correctness, the spec should address how those are replicated for kimi backends — likely by moving hook logic into the runtime itself rather than relying on Claude Code's hook system.
