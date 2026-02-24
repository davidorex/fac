# Research Request: kimi-cli Interface & Capabilities

**Requested by:** spec
**Date:** 2026-02-24
**Blocks:** specs/drafting/multi-cli-backend-support.md

## What I Need to Know

I'm speccing multi-backend support for the factory runtime. The factory currently invokes agents via Claude Code CLI (`claude -p`). The intent is to add kimi-cli as an alternative backend.

### Questions

1. **CLI interface**: What is the kimi-cli invocation pattern? Equivalent of `claude -p --system-prompt "..." --output-format stream-json`? What flags control model selection, system prompt injection, output format?

2. **Tool execution**: Does kimi-cli support native tool use (function calling with local execution)? Claude Code provides built-in Read, Write, Edit, Bash, Glob, Grep tools — does kimi-cli have equivalents, or does it only do text-in/text-out?

3. **Streaming**: Does kimi-cli support streaming output? If so, what is the event schema? (Claude Code uses `stream-json` with event types: `assistant`, `result`, `system`)

4. **Model identifiers**: What model names/aliases does kimi-cli accept?

5. **Permission model**: Does kimi-cli have any equivalent to Claude Code's `--permission-mode`, `--allowedTools`, `--add-dir`?

### Why This Matters

The answers determine whether multi-backend support is:
- **A)** A backend abstraction layer (swap CLI commands and event parsers) — if kimi-cli has native tool execution
- **B)** A fundamental runtime architecture change (implement agentic tool-execution loop) — if kimi-cli is text-in/text-out only

The spec cannot be finalized without this.
