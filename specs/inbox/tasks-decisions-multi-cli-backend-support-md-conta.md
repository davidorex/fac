# tasks-decisions-multi-cli-backend-support-md-conta

## What I'm Seeing
tasks/decisions/multi-cli-backend-support.md contains duplicate entries for decisions 7.1, 7.2, and 7.3. For each decision, there is one entry marked "resolved" or "auto-resolved" with a decided answer, and immediately below it is a duplicate entry marked "open" with the same decision ID but without resolution. This creates ambiguity about state and may confuse `factory decide` command if it scans for unresolved entries.

## What I Want to See
This observation should be addressed.
