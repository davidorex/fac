# Kimi-CLI Integration Notes

For the full tool capabilities reference including both Claude Code and Kimi-CLI,
see `universe/reference/tool-capabilities.md`.

This document focuses specifically on what changes in the factory runtime to
support kimi-cli as a second backend.

## The Change in llm.py

Current invocation (Claude):
```python
cmd = [claude_bin, "-p", "--model", model, "--system-prompt", system_prompt,
       "--output-format", "text", "--permission-mode", "bypassPermissions"]
result = subprocess.run(cmd, input=user_prompt, capture_output=True, text=True,
                        timeout=600, cwd=workspace)
```

Kimi equivalent:
```python
# Write system prompt to temp agent file
agent_file = write_temp_agent_file(system_prompt)
cmd = ["kimi", "--quiet", "--agent-file", str(agent_file),
       "--prompt", user_prompt]
result = subprocess.run(cmd, capture_output=True, text=True,
                        timeout=600, cwd=workspace)
```

Three differences: system prompt goes to a file, user message goes via flag
instead of stdin, and permission bypass is implicit.

## Agent File Format

```yaml
version: 1
agent:
  extend: default
  system_prompt_path: ./assembled-prompt.md
```

The factory already assembles a complete system prompt in `context.py`. For kimi,
that assembled prompt would be written to a temp markdown file and referenced from
a minimal agent YAML.

## agents.yaml Extension

```yaml
builder:
  role: builder
  backend: kimi        # new field
  model: kimi-k2.5     # model name for this backend
  # ... rest unchanged
```

The `backend` field tells `llm.py` which dispatch path to use. Default: `claude`.

## Skills Cross-Compatibility

Kimi-cli discovers skills from `~/.kimi/skills/`, `~/.claude/skills/`, and
`.agents/skills/`. The SKILL.md format with YAML frontmatter is shared. The
factory's existing skills should work with either backend without modification.

## What Kimi Adds

- **CreateSubagent** — define new subagent types at runtime (not just use
  predefined ones). Could enable dynamic specialization.
- **Flow Skills** — executable flowcharts in SKILL.md using Mermaid or D2.
  Multi-step workflows that the AI executes automatically through decision
  points. More structured than plain-text skill instructions.
- **K2.5 multimodal** — native vision and language, 1T parameter MoE. Different
  cognitive profile than Claude models.
- **Agent Swarm** — up to 100 parallel agents (web UI only for now, CLI coming).

## What Kimi Lacks (vs Claude Code)

- No git worktrees (no `--worktree` flag)
- No hooks system (no PreToolUse/PostToolUse lifecycle events)
- No agent teams (peer-to-peer coordination)
- Agent swarm not yet in CLI
- No `--append-system-prompt` (must replace entirely via agent file)
