# Review: hello-world

## Spec
`specs/ready/hello-world.md`

## Artifact
`projects/hello-world/hello.py`

## Verification Results

| Criterion | Command | Outcome |
|-----------|---------|---------|
| No-arg greeting | `python hello.py` | `Hello from the factory! 2026-02-24 02:33:59` — exit 0 ✓ |
| Named greeting | `python hello.py --name World` | `Hello, World, from the factory! 2026-02-24 02:33:59` — exit 0 ✓ |
| Empty name rejection | `python hello.py --name ""` | argparse error, exit 2 ✓ |

## Notes

- Standard library only (`argparse`, `datetime`) — no third-party imports.
- Empty string detection added explicitly since argparse does not natively reject empty strings; `parser.error()` used to produce argparse-style error output and exit 2.
