Start the factory. Check the inbox, run agents through the pipeline, show what's happening.

Do all of this without asking questions. Just go.

1. Check what's in the pipeline:
```bash
echo "=== inbox ===" && ls /Users/david/Projects/fac/factory/specs/inbox/ 2>/dev/null
echo "=== drafting ===" && ls /Users/david/Projects/fac/factory/specs/drafting/ 2>/dev/null
echo "=== ready ===" && ls /Users/david/Projects/fac/factory/specs/ready/ 2>/dev/null
echo "=== tasks/building ===" && ls /Users/david/Projects/fac/factory/tasks/building/ 2>/dev/null
echo "=== tasks/review ===" && ls /Users/david/Projects/fac/factory/tasks/review/ 2>/dev/null
```

2. Based on what you find, run the appropriate agents in order:
   - If inbox has files → run spec: `cd /Users/david/Projects/fac/factory && .venv/bin/factory run spec`
   - If ready has files → run builder: `cd /Users/david/Projects/fac/factory && .venv/bin/factory run builder`
   - If review has files → run verifier: `cd /Users/david/Projects/fac/factory && .venv/bin/factory run verifier`
   - If research requests exist → run researcher first: `cd /Users/david/Projects/fac/factory && .venv/bin/factory run researcher`
   - If nothing needs doing, say so.

3. After each agent finishes, check the pipeline again and run the next agent if work has moved forward. Keep going until the pipeline is idle.

4. Summarize what happened at the end.