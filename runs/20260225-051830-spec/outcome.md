# Outcome

Inbox is empty. One spec in drafting — `multi-cli-backend-support` — was blocked on research that has now returned.

**What I did:** Consumed the research brief and drafted a full NLSpec. The architecture is confirmed: kimi-cli has native tool execution, so this is a thin dispatch layer in `llm.py`, not a fundamental rewrite. The spec covers behavioral requirements, interface boundaries, constraints, out-of-scope, and verification criteria.

**What's blocking ready status:** Three ambiguities need human decisions before this can move to `specs/ready/`:

1. **The hooks gap (high impact):** kimi-cli has no equivalent to Claude Code's PreToolUse/PostToolUse hooks. Factory governance — mandate enforcement, cleanup hooks — won't fire for kimi-backed agents. Options are: accept the gap (system prompt still has the rules, just no enforcement), move critical hook logic into the runtime itself, or defer the question.

2. **Streaming vs text mode for kimi:** Text mode (`--print --final-message-only`) is simpler but the operator loses real-time visibility into kimi agent activity. Streaming needs a kimi-specific event parser but matches the Claude experience.

3. **Model name validation:** Whether the runtime should reject obviously wrong provider/model combinations (e.g., `provider: kimi, model: sonnet`) upfront, or let the backend fail naturally with its own error.
