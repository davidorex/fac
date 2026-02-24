---
name: monitoring
description: How to check if deployed projects are healthy. What "healthy" means per project type.
---

## What "Healthy" Means by Project Type

**CLI tool** — healthy if:
- The entry point runs without error on a known-good input
- The installed version matches the expected version

**Web API / service** — healthy if:
- The health endpoint (e.g., `/health` or `/ping`) returns 200
- Response latency is within expected bounds
- Error rate (5xx responses) is below 1% in the last hour

**Data pipeline** — healthy if:
- The last run completed without errors
- Output data volume is within expected range (sudden drops indicate upstream issues)
- No stale data: last run was within the expected interval

**Background worker / scheduled job** — healthy if:
- Last execution timestamp is within the expected schedule window
- No error entries in the job log since last successful run

## Monitoring Checklist (Heartbeat)

On each hourly heartbeat, for each active deployed project:

1. Identify project type
2. Apply the "healthy" definition above
3. If unhealthy: write a maintenance task to `tasks/maintenance/{project}-{YYYY-MM-DD}-health.md`
   with: what was checked, what was found, suggested remediation

Do not attempt automated remediation without a maintenance task being created first.
The human decides whether to act on a health alert.

## Alerting Threshold

Write a maintenance task for:
- Any health check that fails twice in a row (not just once — transient failures happen)
- Any security advisory that affects a deployed project
- Any CI failure on main that has persisted more than 24 hours

A single transient failure is noted in the daily log but does not create a task.
