# multi-cli-backend-support

## Status: BLOCKED — awaiting research on kimi-cli interface

## What I'm Seeing
The factory currently runs on Claude Code. Kimi-cli is also available as a CLI tool. The factory process is coupled to Claude Code as its sole execution backend.

## What I Want to See
A user can run the factory process with either Claude Code or kimi-cli, losing no functionality. This serves two purposes: managing token costs by choosing backends strategically, and laying the groundwork for routing different parts of the factory to different models.

## Spec Agent Analysis (2026-02-24)

### Coupling Surface Identified
All coupling lives in `runtime/factory_runtime/llm.py`:
- `_find_claude_cli()` — binary discovery, hardcoded to `claude`
- `_model_alias()` — model name mapping, Claude-only
- `run_agent()` — command construction with Claude Code-specific CLI flags
- `_format_event()` — stream-json event parsing, Claude Code schema
- `_build_allowed_tools()` — Claude Code tool names

### Existing Forward-Thinking
`AgentConfig.provider` field exists in config.py (defaults to "anthropic") but is unused in the execution path. The schema already anticipated multiple backends.

### Open Questions (research needed)
1. What is kimi-cli's CLI interface? Flags, input mode, output/streaming format.
2. Does kimi-cli provide native tool execution (file read/write, shell access)? This determines whether the abstraction is "swap CLI commands" or "implement a tool-execution loop."
3. What model identifiers does kimi-cli accept?
4. Does "losing no functionality" mean feature parity on Day 1, or graceful degradation where a backend lacks a capability?

### Architecture Fork
The answer to question 2 determines two very different designs:
- **If kimi-cli has native tool execution:** The abstraction is a Backend protocol with per-backend CLI command builders and event parsers. Relatively contained.
- **If kimi-cli does NOT have native tool execution:** The runtime needs an agentic loop — parse model output for tool calls, execute tools locally, feed results back. This is a much larger change.
