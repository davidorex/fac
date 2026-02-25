# Builder Notes — multi-cli-backend-support

## What was built

Backend dispatch abstraction for the factory runtime. `llm.py` is now
a dispatcher; actual CLI invocation lives in `backends/`.

## File layout delivered

```
runtime/factory_runtime/
  llm.py                       — dispatcher (was monolithic)
  backends/
    __init__.py                — registry: get_backend(provider) → module
    common.py                  — shared: ANSI colors, _short_path, _format_tool_use
    anthropic.py               — Claude Code CLI backend (extracted from old llm.py)
    kimi.py                    — kimi-cli backend (new)
    capabilities.md            — per-backend capability matrix
```

## Behavioral preservation (anthropic)

The Claude Code execution path was extracted without behavioral change.
The same command structure, stdin delivery, stream-json parsing, and
tool formatting are in place. The only observable difference: the run
header now prints `(model, provider: anthropic)`.

## kimi-cli backend

- Uses `kimi-cli` binary (not `kimi`, which aliases to kimi-amos in shells)
- Writes temp agent YAML to `/tmp/factory-agent-{uuid8}.yaml` per run
- Writes temp system prompt to `/tmp/factory-prompt-{uuid8}.md` per run
- Both cleaned up in `finally` block — timeout and exception paths included
- `--print --output-format text -p "user_prompt"` invocation
- `shell_access: none` → `kimi_cli.tools.shell:Shell` in `exclude_tools`

## Governance

`run_pre_governance()` loads mandates from `~/.claude/mandates.jsonl`
and `{workspace}/.claude/mandates.jsonl`. Injects formatted mandate
text into system_prompt before backend dispatch. For the anthropic
backend this is redundant with Claude Code hooks — intentionally so.
`run_post_governance()` is a pure seam: logs metadata, no checks yet.

## Startup validation

`validate_providers(config)` called in `factory run` before dispatch.
Checks each unique provider's binary discoverability. Missing binaries
produce console warnings, do not block agents using working backends.

## One decision made during build

The governance pre-hook injects mandates into the full assembled
system_prompt (including ACL text). The run_logger logs context
*before* mandate injection so the log captures exactly what
`assemble_context()` produced. The mandates appear in the agent file
written to disk. This ordering is intentional: log the base context,
then augment with governance, then dispatch.

## Verification against spec criteria

1. ✅ `provider: kimi` → kimi-cli dispatched, final output returned
2. ✅ `provider: anthropic` → identical live-streaming behavior
3. ✅ `provider: nonexistent` → ValueError: "Available backends: anthropic, kimi"
4. ✅ Missing kimi-cli → warning printed, anthropic agents unaffected
5. ✅ Pre-governance fires for kimi (mandate text in system_prompt → temp file)
6. ✅ Post-governance seam fires (logged in run log via run_logger)
7. ✅ Temp files cleaned in finally block (happy, error, timeout paths)
8. ✅ No new dependencies (yaml, uuid, subprocess — all stdlib or existing)
9. ✅ backends/capabilities.md documents the matrix

## Known gaps (per spec, documented)

- Per-tool-call governance for kimi: not feasible without hook system.
  Mitigated by mandate injection and post-run seam. Documented in
  capabilities.md under "Per-Tool-Call Governance Gap (kimi)".
- kimi streaming: text-only initially. kimi's stream-json uses a
  different schema (conversation-turn JSONL vs Claude event-type JSONL)
  and needs a separate parser. Follow-up if operator visibility is needed.
