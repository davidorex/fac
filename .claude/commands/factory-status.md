Show the current state of the factory pipeline. Run:

```bash
cd /Users/david/Projects/fac/factory && .venv/bin/factory status
```

Then also show what's in each pipeline stage:

```bash
echo "=== specs/inbox ===" && ls /Users/david/Projects/fac/factory/specs/inbox/ 2>/dev/null
echo "=== specs/drafting ===" && ls /Users/david/Projects/fac/factory/specs/drafting/ 2>/dev/null
echo "=== specs/ready ===" && ls /Users/david/Projects/fac/factory/specs/ready/ 2>/dev/null
echo "=== specs/archive ===" && ls /Users/david/Projects/fac/factory/specs/archive/ 2>/dev/null
echo "=== tasks/building ===" && ls /Users/david/Projects/fac/factory/tasks/building/ 2>/dev/null
echo "=== tasks/review ===" && ls /Users/david/Projects/fac/factory/tasks/review/ 2>/dev/null
echo "=== tasks/verified ===" && ls /Users/david/Projects/fac/factory/tasks/verified/ 2>/dev/null
echo "=== tasks/failed ===" && ls /Users/david/Projects/fac/factory/tasks/failed/ 2>/dev/null
```

Summarize the state concisely for the user.