# Backend Capabilities Matrix

Documents what each factory backend supports. Use this when deciding
which agents to route to each backend.

## Capability Comparison

| Capability | anthropic | kimi |
|---|---|---|
| Live streaming | ✓ (stream-json, event-type schema) | ✗ (text-only initially) |
| Per-tool-call governance hooks | ✓ (PreToolUse / PostToolUse via Claude Code) | ✗ (no hook system) |
| Inline system prompt | ✓ (--system-prompt flag) | ✗ (agent YAML file required) |
| Tool-level allow-listing | ✓ (--allowedTools CLI flag) | ✓ (agent file tools / exclude_tools) |
| Model aliasing | ✓ (opus, sonnet, haiku) | ✗ (model names passed through directly) |
| User prompt delivery | stdin (print mode reads stdin) | -p flag argument |
| Binary name | claude | kimi-cli |
| Auto-approval in print mode | ✓ (via Claude Code permission mode) | ✓ (--print implicitly enables --yolo) |
| Session persistence | opt-in (--no-session-persistence default) | not applicable |

## Per-Tool-Call Governance Gap (kimi)

kimi-cli has no hook system. There is no equivalent of Claude Code's
PreToolUse or PostToolUse hooks. For kimi-backed agents:

- **Mitigation 1**: Pre-execution governance injects mandate text into
  the system prompt, establishing behavioral expectations before the run.
- **Mitigation 2**: Post-execution governance (seam) can validate the
  output after the run completes.
- **Accepted gap**: Any governance violation during execution is detected
  only post-run, not at the tool call boundary.

Restrict kimi-backed agents to lower-risk roles (researcher, librarian)
until the post-run governance seam has substantive checks implemented.

## Operator Visibility Gap (kimi)

kimi-cli text-only mode means no live streaming. The operator sees no
activity during long kimi runs. The run log captures stderr and the
final result, but there is no intermediate event stream.

A streaming follow-up can add kimi's stream-json parsing (conversation-
turn JSONL schema, different from Claude Code's event-type schema).

## Binary Discovery

| Backend | Primary | Fallback paths |
|---|---|---|
| anthropic | `claude` (PATH) | `~/.local/bin/claude`, `/usr/local/bin/claude` |
| kimi | `kimi-cli` (PATH) | `~/.local/bin/kimi-cli`, `/usr/local/bin/kimi-cli` |

Note: `kimi` (without `-cli`) is a shell alias for `kimi-amos` in
interactive shells. The factory uses `kimi-cli` to avoid this ambiguity.
In non-interactive subprocess invocation the alias is not active, but
using the explicit binary name is unambiguous in all contexts.
