# Tool Capabilities Reference

This document catalogs the full capabilities of the LLM backends available to
factory agents. It is a living reference — as these tools evolve, this document
should be updated. Agents should consult this when designing solutions, choosing
implementation strategies, or proposing process improvements.

Last updated: 2026-02-24

---

## Claude Code

Version: v2.1+
Binary: `claude`
Invocation: `claude -p --output-format text --system-prompt "..." --model <model>`
Input: user message via stdin
Models: claude-opus-4-6 (1M context beta, 128K output), claude-sonnet-4-5, claude-haiku-4-5

### Print Mode

Non-interactive single-query execution. The factory's primary invocation pattern.

```
claude -p \
  --system-prompt "..." \
  --model opus \
  --output-format text \
  --permission-mode bypassPermissions \
  --no-session-persistence
```

stdin receives the user message. stdout returns the response text.

Flags of note:
- `--system-prompt "text"` or `--system-prompt-file path` — full replacement
- `--append-system-prompt "text"` — adds to built-in prompt (mutually exclusive with replacement)
- `--output-format json` — structured output with metadata
- `--output-format stream-json` — streaming JSONL
- `--tools "Bash,Read,Edit"` — restrict available tools
- `--disallowedTools "WebSearch"` — remove specific tools (works with bypassPermissions; --allowedTools does not)
- `--worktree name` or `-w name` — create isolated git worktree
- `--continue` / `-c` — resume most recent session
- `--resume <id>` / `-r <id>` — resume specific session
- `--agents '<json>'` — define custom subagents dynamically

### Built-in Tools

Claude Code provides its own tool suite. When invoked via `claude -p`, these
tools are available to the agent without any factory-side tool definitions.

**File Operations**
- Read — text files, images, PDFs (with page ranges), Jupyter notebooks
- Write — create new files (overwrites if exists)
- Edit — precise string replacement in existing files, with replace_all option
- MultiEdit — multiple edits in one call
- NotebookEdit — Jupyter cell insert/replace/delete

**Code Search**
- Glob — fast file pattern matching (`**/*.py`, `src/**/*.ts`)
- Grep — ripgrep-based content search, regex, file type filters, context lines

**Execution**
- Bash — persistent shell session, timeout up to 10 min, working directory persists between calls

**Web**
- WebSearch — search engine queries, returns results with links
- WebFetch — fetch URL content, processes with focused prompt, returns answers (not raw HTML)

**Task Management**
- TodoWrite/TodoRead — structured task list with pending/in_progress/completed states

**Orchestration**
- Task — spawn subagents (see Multi-Agent section below)

### Multi-Agent Capabilities

#### Subagents (Task Tool)

The Task tool spawns specialized subagents in isolated context windows.

Built-in subagent types:
- **Explore** — fast codebase search, read-only
- **Plan** — architecture and implementation planning
- **Bash** — command execution specialist
- **general-purpose** — full tool access for complex tasks

Up to 7 subagents can run in parallel. Each gets its own context window with a
custom system prompt. They cannot see the parent's conversation history — all
necessary context must be passed in the task prompt.

Custom subagents can be defined with:
- Custom system prompts
- Tool restrictions
- Independent permission modes
- Focused skills
- Model routing (cheaper models for simpler tasks)

#### Agent Teams (Experimental)

Enable: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

Unlike subagents, agent teams are peer-to-peer:
- One session acts as team lead
- Teammates work independently in separate context windows
- Teammates can communicate directly with each other (not mediated by lead)
- Can share context, challenge approaches, converge on solutions
- True parallel development with coordination

Best for: research, competing hypotheses, cross-layer coordination.

#### Git Worktrees

`claude --worktree feature-name` or `claude -w feature-name`

Creates an isolated working directory and branch for parallel work:
- Independent file state per worktree
- No edit bleeding between sessions
- Auto-cleanup if no changes on exit
- Prompt to keep if commits exist

Multiple Claude Code sessions can work the same repo simultaneously without
conflicts by using separate worktrees.

### Hooks System

Hooks run shell commands at specific lifecycle points. Configured in settings files.

Available hook events:
- **PreToolUse** — before tool execution (validate, block, or modify inputs)
- **PostToolUse** — after tool completion (cleanup, formatting, testing)
- **UserPromptSubmit** — when user sends a message
- **PermissionRequest** — when permission is needed
- **Stop** — when agent finishes responding
- **SubagentStop** — when a subagent finishes
- **SessionEnd** — when session terminates
- **Setup** — for repository initialization

Hook types: `command` (bash) or `prompt` (LLM evaluation).
Communication: stdout, stderr, exit codes. Event data as JSON on stdin.

PreToolUse hooks (v2.0.10+) can modify tool inputs before execution — not just
block them. This enables transparent sandboxing and parameter correction.

### MCP (Model Context Protocol)

Claude Code connects to MCP servers — local programs that bridge to external tools.

Configuration: `.mcp.json` at project root, or passed programmatically.
Protocol: stdio-based.

MCP servers provide access to: Linear, GitHub, Slack, Notion, databases, custom
APIs, and any tool that implements the MCP server protocol.

Tool search: dynamically loads MCP tools on demand when tool descriptions would
consume >10% of context window.

### Memory and Context

**CLAUDE.md** — persistent instructions file read at session start. Include
project patterns, preferences, rules. Recommended over conversation history for
persistent context. Can include "Compact Instructions" section to control what
survives compaction.

**Auto Memory** — automatically saves useful patterns and preferences across
sessions without manual intervention.

**Session Memory** — continuously writes summaries in background. Makes `/compact`
instant (loads pre-written summary instead of re-analyzing).

**Auto-Compaction** — triggers automatically near context limit. Summarizes
history while preserving essential information.

**Session Persistence** — conversations auto-saved as JSONL in
`~/.claude/projects/`. Resume with `-c` (latest) or `-r <id>` (specific).

### Configuration

**User settings**: `~/.claude/settings.json` (global)
**Project settings**: `.claude/settings.json` (shared) or `.claude/settings.local.json` (personal)

Controls: tool permissions (allow/ask/deny), sandbox behavior, environment
variables, hook definitions, MCP servers. Supports JSON schema for editor
autocomplete.

### SDK (Claude Agent SDK)

Package: `@anthropic-ai/claude-agent-sdk` (TypeScript/npm)
Repo: `anthropics/claude-agent-sdk-typescript`

Enables using Claude Code as a library in Node.js applications. Full programmatic
control over agent lifecycle, tool access, sessions, and configuration.

Agent Skills (December 2025): open standard at agentskills.io. Organized packages
of instructions, scripts, and reference materials. Integrated with Messages API
via `/v1/skills` endpoint.

### IDE Integrations

- **VS Code** — official extension with native chat panel, checkpoint undo, inline diffs, parallel conversations
- **JetBrains** — beta plugin for IntelliJ, WebStorm, PyCharm. Quick launch: Cmd+Esc / Ctrl+Esc

---

## Kimi-CLI

Version: 1.12.0+
Binary: `kimi` (or `kimi-cli`)
Invocation: `kimi --quiet --agent-file agent.yaml --prompt "message"`
Input: `--prompt` flag (not stdin)
Models: Kimi K2, Kimi K2.5 (1T params MoE, multimodal, agent swarm)

### Print Mode

```
# Full form
kimi --print --output-format text --final-message-only --prompt "message"

# Shortcut (equivalent)
kimi --quiet --prompt "message"

# With system prompt
kimi --quiet --agent-file agent.yaml --prompt "message"
```

`--quiet` = `--print` + `--output-format text` + `--final-message-only`

Print mode implicitly enables auto-approval (like YOLO). When `--agent-file` is
used, YOLO is also auto-enabled.

Additional flags:
- `--output-format stream-json` — JSONL streaming
- `--output-format json` — structured JSON
- `--input-format stream-json` — accept JSONL input
- `--config-file path` — alternative config
- `--config '{...}'` — inline config as JSON/TOML
- `--mcp-config-file path` — MCP server config
- `--yolo` — auto-approve all operations

### Built-in Tools

**File Operations**
- ReadFile — max 1000 lines per read, max 2000 chars/line
- ReadMediaFile — images/videos up to 100MB (requires vision model)
- WriteFile — create/overwrite (requires approval)
- StrReplaceFile — string replacement editing (requires approval)
- Glob — pattern matching, max 1000 results
- Grep — text search within files

**Web**
- SearchWeb — web search (requires service configured)
- FetchURL — fetch web page content

**Execution**
- Shell — bash/zsh on Unix, PowerShell on Windows (requires approval)

**Orchestration**
- Task — delegate to subagents in isolated contexts
- CreateSubagent — dynamically define new subagent types at runtime (not enabled by default)
- SetTodoList — task management

### Multi-Agent Capabilities

#### Subagents (Task Tool)

Same pattern as Claude Code: delegate tasks to specialized subagents in isolated
contexts. All necessary information must be in the task prompt.

#### CreateSubagent

Unique to kimi-cli: dynamically define new subagent types at runtime. Not enabled
by default.

#### Agent Swarm (K2.5, Web UI only)

Up to 100 parallel agents coordinated by the K2.5 model. Currently available in
the web UI, not yet in CLI. When it arrives in CLI, this would enable massive
parallel task execution.

### Agent Files

System prompts via YAML definition files:

```yaml
version: 1
agent:
  extend: default
  system_prompt_path: ./my-prompt.md
  exclude_tools:
    - "kimi_cli.tools.web:SearchWeb"
    - "kimi_cli.tools.web:FetchURL"
```

The `extend: default` line inherits the default agent's tools and behavior.
Tools can be selectively excluded. System prompt loaded from a file path.

### MCP Support

Full MCP server integration:
- Config: `~/.kimi/mcp.json` (compatible with Claude Code's MCP format)
- CLI management: `kimi mcp` subcommand
- Ad-hoc: `--mcp-config-file` flag
- All MCP tool calls follow the same approval flow (auto-approved in YOLO/print)

### Skills System

Skills auto-discovered from:
- `~/.kimi/skills/`
- `~/.claude/skills/` (cross-compatible)
- `.agents/skills/` (project-level)

Format: directories containing SKILL.md with YAML frontmatter. Names, paths,
descriptions auto-injected into system prompt. AI decides when to read the full
SKILL.md.

**Flow Skills**: embed executable flowcharts (Mermaid or D2) in SKILL.md for
multi-step automated workflows. More powerful than static prompts for complex
procedures.

### Memory and Context

- Sessions stored in `~/.kimi/sessions/` as JSONL
- Auto-compaction when approaching token limits
- **D-Mail**: checkpoint-based time travel — revert to previous conversation points
- Session resume preserves full conversation history

### Configuration

Primary: `~/.kimi/config.toml` (TOML preferred, JSON legacy auto-migrated)

```toml
[provider.moonshot]
api_key = "key"
model = "kimi-k2.5"

[default_yolo]
true

[[services]]
name = "web_search"
[[services]]
name = "web_fetch"
```

Environment variables: `KIMI_API_KEY`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`

### SDK (Kimi Agent SDK)

Repo: `MoonshotAI/kimi-agent-sdk`
Languages: Python, Node.js/TypeScript, Go

Thin client that proxies to CLI runtime. Reuses CLI sessions, configs, tools.
Two API levels: high-level Prompt API (simple) and low-level Session API (full
control).

---

## Invocation Pattern Comparison

| Concern | Claude Code | Kimi-CLI |
|---|---|---|
| Binary | `claude` | `kimi` |
| Print mode | `-p` | `--quiet` |
| System prompt | `--system-prompt "text"` | `--agent-file path.yaml` |
| User message | stdin pipe | `--prompt "text"` flag |
| Output format | `--output-format text` | included in `--quiet` |
| Permission bypass | `--permission-mode bypassPermissions` | auto with `--agent-file` / `--yolo` |
| Model selection | `--model opus` | set in config/agent file |
| Tool restriction | `--disallowedTools "X"` | `exclude_tools` in agent file |
| Worktrees | `--worktree name` | not available |
| Session resume | `--continue` / `--resume id` | `/sessions` command |
| Subagents | Task tool (up to 7 parallel) | Task tool + CreateSubagent |
| Agent teams | experimental (env var) | Agent Swarm (web UI only) |
| MCP config | `.mcp.json` | `~/.kimi/mcp.json` (compatible format) |
| Skills discovery | CLAUDE.md, skills dirs | `~/.kimi/skills/`, `~/.claude/skills/`, `.agents/skills/` |

### Key Differences

1. **Input method**: Claude reads from stdin; kimi uses `--prompt` flag. Subprocess invocation differs.
2. **System prompt delivery**: Claude takes inline string; kimi takes file reference. Factory must write temp agent files for kimi.
3. **Worktrees**: Claude-only feature. Enables parallel repo work without conflicts.
4. **Agent teams vs swarm**: Claude has experimental peer-to-peer teams; kimi has swarm (100 agents) but web-only.
5. **CreateSubagent**: Kimi can define new subagent types at runtime. Claude defines them via `--agents` JSON flag.
6. **Skills cross-compatibility**: Kimi reads from `~/.claude/skills/` — the skill format is shared.
7. **Flow skills**: Kimi-only. Executable flowcharts embedded in SKILL.md for multi-step workflows.

---

## What This Means for Factory Agents

The factory runtime (`llm.py`) shells out to `claude -p`. Supporting kimi-cli
requires:

1. Writing the assembled system prompt to a temp YAML agent file instead of passing inline
2. Passing the user message via `--prompt` flag instead of stdin
3. Reading a `backend` field from agents.yaml to dispatch to the right binary

The tool capabilities are nearly identical — both provide file I/O, shell
execution, web access, and subagent orchestration. The factory's access control
rules (prompt-based) work with either backend since they're injected into the
system prompt.

Multi-model assignment becomes an experimental axis: which cognitive profiles
(reasoning vs execution vs curation) map best to which backends and models.

### Capabilities Agents Should Know About

When designing solutions, agents have access to these backend capabilities whether
or not the factory's own tool definitions expose them:

- **Parallel subagents** — break large tasks into concurrent subtasks
- **Git worktrees** — work on multiple branches simultaneously (Claude only)
- **MCP servers** — connect to external tools and data sources
- **Web search and fetch** — research without leaving the agent loop
- **Hooks** — automate pre/post processing around tool calls (Claude only)
- **Flow skills** — executable multi-step workflows (Kimi only)
- **Streaming output** — JSONL for real-time progress monitoring
- **Session resume** — pick up where a previous run left off

These are the proteins the factory can build from. The more agents understand
about their own tools, the better solutions they can design.
