# Outcome

Research brief delivered. Here's the summary:

**Picked up**: `tasks/research/spec-kimi-cli-interface-v2.md` (re-filing — original brief didn't persist)
**Delivered**: `tasks/research-done/spec-kimi-cli-interface-v2.md`
**Unblocks**: `specs/drafting/multi-cli-backend-support.md`

**Key findings:**
- kimi-cli v1.12.0 has full native tool execution (10+ tools). Backend abstraction approach is correct.
- Factory invocation: `kimi-cli --print --agent-file /tmp/agent.yaml -p "message"`
- **No hook system exists** — governance gap is real. Hard gate for operator decision confirmed.
- Use `kimi-cli` binary name (not `kimi`) — shell alias `kimi` → `kimi-amos` (a completely different tool) creates ambiguity.
- `--output-format json` doesn't exist (only `text` and `stream-json`). Stream-json JSONL schema differs from Claude Code's event format.
- 5 inaccuracies identified in `universe/reference/tool-capabilities.md`. Reference docs continue to need empirical verification for implementation-critical details.
