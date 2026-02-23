# Heartbeat Configuration

Add these lines to your crontab to enable automatic agent heartbeats.

## Setup

```bash
# Edit crontab
crontab -e

# Or if running as a dedicated factory user:
# crontab -u factory -e
```

## Crontab Lines

```cron
# Factory Agent Heartbeats
# Activate the venv and run from the workspace directory

FACTORY_WORKSPACE=/Users/david/Projects/fac/factory
FACTORY_VENV=/Users/david/Projects/fac/factory/.venv/bin

# Spec — daily at 8am (first, to catch new intents)
0 8 * * *     cd $FACTORY_WORKSPACE && $FACTORY_VENV/factory run spec     >> runs/cron.log 2>&1

# Researcher — daily at 9am (after spec may have created research requests)
0 9 * * *     cd $FACTORY_WORKSPACE && $FACTORY_VENV/factory run researcher >> runs/cron.log 2>&1

# Builder — every 30 minutes (picks up ready specs)
*/30 * * * *  cd $FACTORY_WORKSPACE && $FACTORY_VENV/factory run builder   >> runs/cron.log 2>&1

# Verifier — every 15 minutes (checks for completed work)
*/15 * * * *  cd $FACTORY_WORKSPACE && $FACTORY_VENV/factory run verifier  >> runs/cron.log 2>&1

# Operator — hourly (git, CI, dependencies)
0 * * * *     cd $FACTORY_WORKSPACE && $FACTORY_VENV/factory run operator  >> runs/cron.log 2>&1

# Librarian — nightly at 10pm (review learnings, proposed skills, memory hygiene)
0 22 * * *    cd $FACTORY_WORKSPACE && $FACTORY_VENV/factory run librarian >> runs/cron.log 2>&1
```

## Notes

- The ANTHROPIC_API_KEY environment variable must be available to cron jobs.
  Add it to your shell profile or set it in the crontab header:
  ```
  ANTHROPIC_API_KEY=sk-ant-...
  ```

- Heartbeat runs that find no work produce NO_REPLY and exit cleanly.

- If an agent produces NO_REPLY on 3 consecutive heartbeats with no
  filesystem changes in between, consider reducing its frequency to
  avoid wasting tokens on idle checks.

- Manual invocations (`factory run <agent> --task ...`) work independently
  of the heartbeat schedule. You can always invoke an agent directly.
