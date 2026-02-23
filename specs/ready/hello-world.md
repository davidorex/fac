# NLSpec: hello-world

## Overview

A minimal Python CLI script that greets the user and displays the current date and time. Serves as a first proof-of-life artifact for the factory — a trivially verifiable output that confirms the build pipeline works end to end.

## Behavioral Requirements

- When invoked with no arguments, the script prints `Hello from the factory!` followed by the current local date and time on the same line, then exits with code 0.
- When invoked with `--name Alice`, the script prints `Hello, Alice, from the factory!` followed by the current local date and time on the same line, then exits with code 0.
- The date/time is formatted as `YYYY-MM-DD HH:MM:SS` (24-hour, local timezone).

## Interface Boundaries

### CLI

```
python hello.py [--name NAME]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--name` | No | (none) | A name to include in the greeting |

### Output format

Without `--name`:
```
Hello from the factory! 2026-02-24 02:31:40
```

With `--name Alice`:
```
Hello, Alice, from the factory! 2026-02-24 02:31:40
```

Output goes to stdout. No trailing newline beyond the standard one produced by `print()`. Nothing is written to stderr on success.

### Dependencies

- Python 3.8+ standard library only. No third-party packages.
- Uses `argparse` for argument parsing and `datetime` for timestamp.

### File location

The script is created at `projects/hello-world/hello.py` within the factory workspace.

## Constraints

- No third-party dependencies. Standard library only.
- The `--name` flag value must be a non-empty string. If `--name` is passed with an empty string, argparse's default behavior (raising an error) is acceptable.
- The script must not read from stdin or modify any files.
- No interactive prompts.

## Out of Scope

- Logging, configuration files, or environment variable support.
- Localization or timezone selection.
- Any output format other than plain text to stdout.
- Test files (verification is behavioral, per criteria below).

## Verification Criteria

- Running `python hello.py` produces a line matching the pattern `Hello from the factory! YYYY-MM-DD HH:MM:SS` and exits 0.
- Running `python hello.py --name World` produces a line matching `Hello, World, from the factory! YYYY-MM-DD HH:MM:SS` and exits 0.
- Running `python hello.py --name ""` exits non-zero or produces an argparse error (either is acceptable).
- The script contains no imports outside the Python standard library.
