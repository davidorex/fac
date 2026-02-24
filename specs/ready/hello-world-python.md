# hello-world-python

## 1. Overview

A single-file Python script that prints "Hello, World!" to stdout. This spec exists as an end-to-end test of the Factory pipeline — from intent through spec, build, and verification. The deliverable is trivial by design; the value is in exercising the pipeline.

## 2. Behavioral Requirements

- When the script is executed via `python hello_world.py`, it prints exactly `Hello, World!` (followed by a newline) to stdout and exits with code 0.
- When the script is executed directly via `./hello_world.py` (given executable permissions), the behavior is identical.
- The script performs no other I/O — no file reads, no network calls, no prompts.

## 3. Interface Boundaries

### CLI interface

```
python hello_world.py
# or
./hello_world.py
```

No arguments, no flags, no options. Any arguments passed are silently ignored.

### Output format

Exact stdout output (no trailing whitespace, single trailing newline):

```
Hello, World!
```

Exit code: `0`

### File location

`projects/hello-world-python/hello_world.py`

## 4. Constraints

- Python 3.x (no version-specific features required).
- No external dependencies. No imports beyond what's needed (a bare script with no imports is acceptable; `sys` is acceptable if used).
- Single file. No package structure, no `__init__.py`, no `setup.py`.
- Must include a shebang line: `#!/usr/bin/env python3`
- Must include a module-level docstring explaining what the script does.
- Must have executable file permissions (`chmod +x`).

## 5. Out of Scope

- Test files — Verifier will validate directly against the verification criteria.
- CI/CD configuration.
- Packaging, distribution, or installation mechanisms.
- Any behavior beyond printing the greeting.

## 6. Verification Criteria

- Running `python projects/hello-world-python/hello_world.py` produces exactly `Hello, World!\n` on stdout and exits 0.
- Running `./projects/hello-world-python/hello_world.py` produces identical output (confirms shebang and permissions).
- The file contains a shebang line as its first line.
- The file contains a docstring.
- The file contains no import statements for packages outside the Python standard library.
- `python -m py_compile projects/hello-world-python/hello_world.py` succeeds (valid Python syntax).

## 7. Ambiguities

None. This spec is fully determined.
