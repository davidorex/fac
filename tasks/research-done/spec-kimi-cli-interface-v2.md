# Research Brief: kimi-cli Interface Details (v2)

**Requested by:** spec
**Researched by:** researcher
**Date:** 2026-02-25
**Blocking:** `specs/drafting/multi-cli-backend-support.md`

## Question

What are the empirically verified invocation, tool execution, output format, hook system, and binary details for kimi-cli v1.12.0 that Builder needs to implement the kimi backend?

## Methodology

Universe-first (`universe/reference/tool-capabilities.md`), then empirical verification against the live `kimi-cli v1.12.0` installation. Binary inspection, `--help` output parsing, Python package introspection (`kimi_cli.tools.*`), and official documentation at `moonshotai.github.io/kimi-cli/`.

## Findings

### 1. Invocation Syntax (verified)

Factory invocation pattern:

```bash
kimi-cli --print --output-format text --agent-file /tmp/agent.yaml -p "user message"
```

Or equivalently:

```bash
kimi-cli --quiet --agent-file /tmp/agent.yaml -p "user message"
```

Key flags:
- `--print` — non-interactive mode (implicitly enables `--yolo` for auto-approval)
- `--quiet` — alias for `--print --output-format text --final-message-only`
- `-p` / `-c` / `--prompt` / `--command` — user message as flag argument (NOT stdin)
- Can also pipe via stdin: `echo "message" | kimi-cli --print`
- `--agent-file FILE` — custom agent YAML (system prompt delivery)
- `--model TEXT` / `-m TEXT` — model override (config default: `kimi-code/kimi-for-coding`)
- `--output-format [text|stream-json]` — output format (must use with `--print`)
- `--input-format [text|stream-json]` — input format (must use with `--print`)
- `--mcp-config-file FILE` — MCP server config
- `--thinking` / `--no-thinking` — reasoning mode toggle
- `--max-steps-per-turn N` — step limit per turn

### 2. Tool Execution Model (verified)

Native agentic tool execution confirmed. This supports **Option A** in the spec (backend abstraction, not fundamental architecture change).

Complete tool inventory (from `kimi_cli.tools.*` package inspection):

| Category | Tool Class | Notes |
|---|---|---|
| File I/O | `ReadFile`, `ReadMediaFile`, `WriteFile`, `StrReplaceFile`, `Glob`, `Grep` | ReadFile: max 1000 lines, 2000 chars/line |
| Execution | `Shell` | bash/zsh on Unix |
| Web | `SearchWeb`, `FetchURL` | Requires service config in `~/.kimi/config.toml` |
| Multi-agent | `Task`, `CreateSubagent` | CreateSubagent is unique to kimi |
| Task mgmt | `SetTodoList` | |
| Cognitive | `Think`, `SendDMail` | Think = internal reasoning; SendDMail = checkpoint time-travel |

**Tool authorization**: `--yolo` / `--print` auto-approves all. Agent files control tools via:
- `tools:` — whitelist (full `kimi_cli.tools.module:ClassName` format)
- `exclude_tools:` — blacklist from inherited set

### 3. Output Format (verified)

Two modes only:
- `--output-format text` — plain text final response
- `--output-format stream-json` — JSONL streaming

**No `--output-format json` exists.** The universe reference doc was wrong about this.

Stream-json schema (from official docs):
```json
{"role": "user", "content": "..."}
{"role": "assistant", "content": "...", "tool_calls": [...]}
{"role": "tool", "tool_call_id": "tc_1", "content": "result"}
```

Each JSON object on a separate line. This is a conversation-turn schema — different from Claude Code's event-type schema (`type: "assistant"`, `type: "tool_use"`, etc.). The factory's stream parser would need a kimi-specific implementation.

### 4. Hook System (verified: absent)

**kimi-cli has NO hook/event system.** Confirmed via:
- CLI help output (no hook-related flags)
- Official documentation (no hooks page or mention)
- GitHub repository README (no hooks section)
- Source package inspection (no hooks module)

No PreToolUse, PostToolUse, UserPromptSubmit, or any lifecycle event equivalent exists.

### 5. Binary Name and Discovery (verified, with complication)

| Path | Version | What it is |
|---|---|---|
| `/Users/david/.local/bin/kimi-cli` | 1.12.0 | Moonshot kimi-cli (Python, uv-installed) |
| `/Users/david/.local/bin/kimi` | 1.12.0 | Symlink to same Moonshot kimi-cli |
| `/Users/david/.bun/bin/kimi-amos` | 0.1.0 | **Completely different tool** — custom Bun-based AI assistant |

**Critical**: Shell alias `kimi` → `kimi-amos` (defined in `.zshrc` line 100). In interactive shells, `kimi` runs the wrong binary. In non-interactive subprocess invocation (how the factory calls backends), the alias is NOT active and `kimi` resolves to the Moonshot CLI correctly.

**Factory should use `kimi-cli` as the binary name** — unambiguous in all contexts.

## Agent File Format (verified)

```yaml
version: 1
agent:
  extend: default
  system_prompt_path: ./system-prompt.md
  exclude_tools:
    - "kimi_cli.tools.web:SearchWeb"
    - "kimi_cli.tools.web:FetchURL"
```

System prompt template variables: `${KIMI_NOW}`, `${KIMI_WORK_DIR}`, `${KIMI_WORK_DIR_LS}`, `${KIMI_AGENTS_MD}`, `${KIMI_SKILLS}`. Custom vars via `system_prompt_args:`.

The factory must write a temp agent YAML file for each kimi backend invocation (cannot pass system prompt inline like Claude's `--system-prompt`).

## Reference Doc Corrections

The universe doc (`universe/reference/tool-capabilities.md`) has these inaccuracies:
1. Claims `--output-format json` exists — **doesn't** (only `text` and `stream-json`)
2. Comparison table says sessions use `/sessions` command — actual flags: `--session -S` / `--continue -C` / `--list-sessions`
3. Missing: `--thinking`/`--no-thinking` flag
4. Missing: `Think` and `SendDMail` tools from tool inventory
5. Missing: `--max-steps-per-turn`, `--max-retries-per-step`, `--max-ralph-iterations` flags

Previous daily log (2026-02-24) incorrectly claimed `--quiet` doesn't exist — it does.

## Recommendation

**For spec ambiguity 7.1 (governance hook gap):** The gap is confirmed and real. Recommend **Option (a)** for initial implementation — accept the gap, restrict kimi backend to lower-risk agents (researcher, librarian), enforce governance via system prompt injection. Build the seam for Option (b) later. This remains a hard gate for the operator.

**For spec ambiguity 7.2 (output streaming):** Start with **Option (a)** text-only. kimi-cli does support `stream-json`, so Option (b) is feasible as a follow-up, but the JSONL schema is different from Claude Code's — it will need its own parser.

**For spec section 3.4 (CLI discovery):** Use `kimi-cli` as the binary name, not `kimi`. Avoids the alias complication entirely.

## Trade-offs

- Text-only output means no live streaming for kimi-backed agents initially — operator flies blind during long runs
- No hooks means any governance violation by a kimi-backed agent is detected only post-run
- Agent file requirement adds a temp-file-write step to each kimi invocation (vs. Claude's inline `--system-prompt`)

## Confidence

**High.** All findings verified empirically against the live v1.12.0 installation and cross-referenced with official documentation. Tool inventory confirmed via Python package introspection.

## Sources

- `kimi-cli --help` output (v1.12.0, live on system)
- `kimi_cli.tools.*` package inspection (Python introspection)
- `universe/reference/tool-capabilities.md` (factory reference, cross-checked)
- https://moonshotai.github.io/kimi-cli/ (official docs)
- https://github.com/MoonshotAI/kimi-cli (GitHub repo)
- `~/.kimi/config.toml` (live config)
