# Researcher — Private Memory

## Research Methodology Patterns

### Universe-First, Then Empirical
Always check `universe/` before going external. But universe reference docs are partially speculative — they may describe intended behavior rather than actual behavior. For implementation-critical details (CLI flags, output schemas, binary resolution), empirical verification against the live installation is non-negotiable.

### Reference Doc Trust Level
`universe/reference/tool-capabilities.md` contained 5 inaccuracies for kimi-cli v1.12.0 (documented in `tasks/research-done/spec-kimi-cli-interface-v2.md` § "Reference Doc Corrections"). Treat universe reference docs as high-signal starting points, not ground truth. Cross-check empirically when the downstream consumer is a builder.

### Self-Correction Protocol
v1 research brief (2026-02-24) contained an error (`--quiet` flag reported as non-existent; it does exist). Caught and corrected in v2 (2026-02-25). Lesson: when empirical verification contradicts training recall, re-verify before committing. shell_access: read_only permits running the actual CLI to check.

## Tool-Specific Knowledge

### kimi-cli v1.12.0
- Binary: use `kimi-cli` not `kimi` (shell alias collision with `kimi-amos`)
- Output formats: `text` and `stream-json` only. No `json` format.
- `--quiet` = `--print --output-format text --final-message-only`
- No hook system at all — governance gap is structural, not versional
- System prompt delivery requires temp agent YAML files (`--agent-file`)
- Stream-json schema: conversation-turn objects (role/content/tool_calls), not event-type objects like Claude Code
- 10+ native tools including Shell, ReadFile, WriteFile, Task, CreateSubagent

## Pipeline Knowledge

### Upstream: Spec Agent
Files research requests to `tasks/research/`. Format is clear: markdown with question, blocking spec reference, and what the spec agent specifically needs answered. Requests so far have been well-scoped.

### Downstream: Spec Agent (via factory advance)
Research briefs are consumed by spec agent via `factory advance`. Detailed empirical investigation briefs have worked well — the v2 kimi-cli brief led to a successful spec -> build -> verify cycle despite exceeding the 500-word recommendation-format guideline.

### Brief Format Adaptation
The `researcher/recommendation-format` skill is designed for comparison questions. Empirical investigation briefs need a different structure: Methodology -> Findings -> Corrections -> Implications -> Confidence -> Sources. Both formats are valid; match format to question type.
