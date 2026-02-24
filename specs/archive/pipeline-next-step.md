# pipeline-next-step

## Overview

After `factory run <agent>` completes, the CLI currently prints the agent's response and a run-log path, then returns to the prompt. The operator is left to remember which agent handles the next pipeline stage and whether there's work waiting. This feature adds pipeline-awareness to the CLI's post-run output: when an agent finishes and downstream directories contain work, the CLI prints the next command to run. When nothing is waiting, it says so explicitly.

## Behavioral Requirements

1. **When an agent run completes successfully and one or more downstream pipeline directories contain work items (non-dotfiles), the CLI prints a "next step" block after the run-log line.** Each downstream directory with work gets one line showing the directory, item count, and the `factory run` command that would process it. Format:

   ```
     {directory} has {N} item(s) — next: factory run {agent}
   ```

2. **When an agent run completes successfully and no downstream directories contain work, the CLI prints:**

   ```
     Pipeline idle — nothing waiting downstream.
   ```

3. **When an agent run fails (exception), no next-step output is printed.** The existing error output is sufficient.

4. **When an agent responds with NO_REPLY, the next-step check still runs.** Work may have been waiting from a previous run even if this heartbeat found nothing new to do.

5. **When multiple downstream directories have work, all are listed.** For example, after `factory run spec` completes, if both `specs/ready/` and `tasks/research/` have items, both lines appear.

## Interface Boundaries

### Pipeline Graph

The downstream mapping from agent to directories-to-check is:

| Agent that just ran | Directories to check             | Suggested command          |
|---------------------|----------------------------------|----------------------------|
| spec                | `specs/ready/`                   | `factory run builder`      |
| spec                | `tasks/research/`                | `factory run researcher`   |
| researcher          | `tasks/research-done/`           | *(informational only — no single agent owns this; spec or builder may consume)* |
| builder             | `tasks/review/`                  | `factory run verifier`     |
| verifier            | `tasks/failed/`                  | *(informational only — human decides next action)* |
| verifier            | `tasks/verified/`                | *(informational only — work complete)* |
| librarian           | *(no downstream — curates in place)* | |
| operator            | *(no downstream — maintains in place)* | |

For informational-only entries (no single actionable command), the format is:

```
  {directory} has {N} item(s)
```

No `— next:` suffix.

### Where it happens in the code

The next-step logic runs in `cli.py` inside the `run` command, after the agent response is printed and after the run-log line is printed. It is a new function (suggested name: `print_pipeline_next`) called at that point.

### Counting items

An "item" is any file or directory entry in the target directory whose name does not start with `.` (i.e., excluding `.gitkeep` and other dotfiles). This matches the existing counting logic used in `status()`.

### Output styling

Use `rich` console formatting consistent with the existing CLI:
- The "next:" command portion is bold (`[bold]factory run {agent}[/bold]`)
- Item counts use yellow when > 0 (`[yellow]{N}[/yellow]`)
- The idle message uses dim (`[dim]Pipeline idle — nothing waiting downstream.[/dim]`)

## Constraints

- The pipeline graph must be defined as data, not scattered across conditionals. A dictionary or similar structure that maps `agent_name → list of (directory, suggested_command_or_None)` tuples. This makes it trivial to extend when new agents or pipeline stages are added.
- The feature must not make any additional API calls or read file contents. It only counts directory entries.
- The feature must not change the behavior of the `status` command. `status` already shows pipeline counts; this feature is specifically for the post-`run` context.
- The feature must not slow down the CLI perceptibly. Directory listing is I/O-bounded at microsecond scale; no concern here, but no network calls.

## Out of Scope

- Automatic chaining (running the next agent without human confirmation). The human invokes each step.
- Showing upstream status (what fed into the agent that just ran).
- Modifying the `status` command's output.
- Adding pipeline awareness to any command other than `run`.
- Adding a `factory run all` or `factory run next` command. That may come later but is a separate spec.

## Verification Criteria

- After running `factory run spec` when `specs/ready/` contains a file, the CLI output includes a line mentioning `specs/ready/` and `factory run builder`.
- After running `factory run builder` when `tasks/review/` is empty, the CLI output includes the idle message.
- After running `factory run spec` when both `specs/ready/` and `tasks/research/` contain files, both directories appear in the output.
- After running `factory run librarian`, the idle message appears (librarian has no downstream).
- When an agent run errors out, no next-step block appears.
- The pipeline graph is defined as a single data structure, not spread across conditionals.
