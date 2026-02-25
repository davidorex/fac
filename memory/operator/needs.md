# Operator — Needs & Observations

## operator-not-monitoring-agent-needs-files
- status: open
- created: 2026-02-25T21:01:42Z
- category: observation
- blocked: Six agents (builder, verifier, spec, librarian, researcher, reviewer) have active needs.md files with recent entries (Feb 25, 20:48-21:01), but I have not been reading them. My core function is "Report infrastructure friction to factory needs for the human before it blocks work." I cannot report friction I am not observing. Pattern: all other agents write observations to needs.md on every reflection pass; I have never read them.
- context: Reflection pass. Globbed memory/*/needs.md and found 6 files with timestamps from today; globbed memory/operator/needs.md and found this file did not exist until this moment.

### Exact Change
Operator should establish a daily practice of reading all agents' needs.md files at the start of each session. Prioritize entries marked "blocker" and promoted "high" observations. Consider a new operator skill `shared/infrastructure-monitor` that lists recent needs.md entries by agent and signals which ones are infrastructure vs. cosmetic.

---

## operator-no-daily-logs-established
- status: open
- created: 2026-02-25T21:01:42Z
- category: observation
- blocked: memory/daily/operator/ contains no log files. Context-discipline skill specifies writing daily logs as checkpoints and summaries. After the factory has completed 3 infrastructure specs, hello-world-python, and accumulated 19 factory-internal observations, operator has written zero daily logs. Without logs, there is no audit trail of infrastructure issues noticed, decisions made, or patterns observed. Operator cannot checkpoint context mid-analysis or detect if I am drifting in attention across runs.
- context: Reflection pass. Globbed memory/daily/operator/ and found only .gitkeep.

### Exact Change
Operator should write a daily log entry at the end of each session, capturing: infrastructure observations reviewed, factory-internal issues triaged, any patterns across agent needs.md files, decisions about what to promote/dismiss. This creates continuity for operator context and audit trail for the human.

---

## operator-factory-internal-observations-not-systematically-triaged
- status: open
- created: 2026-02-25T21:01:42Z
- category: observation
- blocked: specs/factory-internal/ contains 19 observations from recent reflection passes. Filesystem shows: 2 "critical" (not found), 3 "high" (2026-02-25T2058-high-*.md, 2026-02-25T2101-high-*.md), remainder "low". My role includes surfacing infrastructure friction, but I have not systematically reviewed these 19 to determine which require human attention, which are auto-resolvable, or what infrastructure improvements they point to.
- context: Reflection pass. Ran `find specs/factory-internal/ -type f | wc -l` to get count and `ls -la specs/factory-internal/` to see severity naming.

### Exact Change
Operator should run `factory triage --list` (or equivalent) to surface open factory-internal observations, then systematically review high-severity ones to decide: promote to inbox specs for building, dismiss with documented reason, or defer with rationale. This is part of monitoring infrastructure state.

---

## operator-decision-file-duplicate-entries
- status: open
- created: 2026-02-25T21:01:42Z
- category: observation
- blocked: tasks/decisions/multi-cli-backend-support.md contains duplicate entries for decisions 7.1, 7.2, and 7.3. For each decision, there is one entry marked "resolved" or "auto-resolved" with a decided answer, and immediately below it is a duplicate entry marked "open" with the same decision ID but without resolution. This creates ambiguity about state and may confuse `factory decide` command if it scans for unresolved entries.
- context: Reflection pass. Read tasks/decisions/multi-cli-backend-support.md (lines 3-65). Duplicate pattern visible at 7.1 (lines 3-8 vs 13-24), 7.2 (lines 25-30 vs 33-44), 7.3 (lines 46-50 vs 54-65).

### Exact Change
The decision file should be de-duplicated: keep only the resolved entries (7.1, 7.2, 7.3 with decided answers), remove the duplicate "open" entries below each. Or, if the format is intentional (showing both state and original question), document this in filesystem-conventions and update the decision writing code to prevent future duplication.

---

## operator-verifier-observation-runtime-code-needs-tests
- status: open
- created: 2026-02-25T21:01:42Z
- category: observation
- blocked: Verifier surfaced that runtime code (factory_runtime/) verification is trace-based (mental code reading), not execution-based. The factory runtime has no test harness — no isolated entry point for testing individual functions, no mock dispatch for backends. This is a structural gap: infrastructure code gets weaker verification than application code. When runtime bugs occur, they will have passed weaker scrutiny than builder-implemented code.
- context: Reflection pass. Read memory/verifier/needs.md entry "verifier-trace-based-verification-for-runtime-code" (lines 47-56).

### Exact Change
This is an architectural issue requiring human decision: either (a) build a minimal test harness for factory_runtime (import checks, function signature validation), or (b) accept that runtime code gets trace-based verification and document this as a known limitation. Not urgent, but infrastructure quality is at stake.

---

## operator-private-memory-should-be-curated
- status: open
- created: 2026-02-25T21:01:42Z
- category: observation
- blocked: My private MEMORY.md is empty (placeholder only). After this reflection pass, I have observed multiple infrastructure patterns: agent needs.md files, factory-internal observations, decision file issues, missing test harness. These are durable operator insights that should be captured for next session. Without curation, each operator session starts cold.
- context: Reflection pass. Read memory/operator/MEMORY.md (lines 1-3), compared against curation pattern in builder and verifier needs.md files.

### Exact Change
At end of operator session, curate MEMORY.md with patterns observed: which agent needs.md entries recur across sessions, which factory-internal observation categories point to the same gap, infrastructure priorities for next human decision. This is identical to the curation pattern other agents should follow.

---

## operator-available-skills-not-activated
- status: open
- created: 2026-02-25T21:01:42Z
- category: observation
- blocked: Operator has 6 available skills (human-action-needed, decomposition, nanoclaw-whatsapp, git-workflow, ci-cd, dependency-management, monitoring) that are directly relevant to "keep the lights on" role, but I have never activated any of them. This is architectural: operator should have these loaded at start of each session if they address ongoing monitoring needs. CI/CD, dependency-management, and monitoring directly support infrastructure health checks — core to operator function.
- context: Reflection pass. Checked git log for "Load skill git-workflow" or similar — no matches. Assumption: skills only loaded when explicitly requested in a turn, and I have not written any turn that requests them.

### Exact Change
Consider whether `git-workflow`, `ci-cd`, `dependency-management`, and `monitoring` should move from `available:` to `always:` in agents.yaml, since operator should be actively monitoring these. Alternatively, create a new operator skill `infrastructure-checkpoint` that loads and runs these four in sequence as part of each operator session.

---

## operator-not-reading-projects-directory
- status: open
- created: 2026-02-25T21:01:42Z
- category: observation
- blocked: Operator can read `projects/` (in can_read scope), but have not checked for CI/CD pipeline health, dependency updates, or build failures in registered projects. Currently have two projects: hello-world-python and hello-world (placeholder). No monitoring of their health or upstream dependencies is happening.
- context: Reflection pass. Operator role includes "CI, dependencies, deployments, monitoring." Access scope includes `projects/`. No git log entries show operator checking project status.

### Exact Change
Operator should establish a session start habit: check each project in projects/ for (a) recent git commits, (b) CI status (if .github/workflows/ exists), (c) dependencies in requirements.txt / package.json, (d) any build artifacts or errors. This is part of "keep the lights on."
