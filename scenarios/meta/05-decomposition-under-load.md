# Scenario 5: Decomposition Under Load

**Title:** Researcher parallelizes a complex investigation

**Story:** A new project requires evaluating 4 competing database solutions. Researcher decomposes.

**Expected trajectory:**

Spec writes a research request: "We need a database for a local-first app with sync. Evaluate SQLite + cr-sqlite, Ditto, PowerSync, and ElectricSQL."

Researcher determines this is a 4-way comparison that would blow its context budget if done serially. It writes 4 subagent tasks, one per database. Each subagent reads the library's docs, checks maintenance status, evaluates the sync model, and writes a structured evaluation.

The 4 subagents run in parallel. Researcher reads all 4 outputs, synthesizes a comparison, and writes a recommendation brief with a clear winner and honest trade-offs.

**Satisfaction criteria:** The parallel execution completes faster than serial would have. Each subagent stays in GREEN zone. The synthesis adds value beyond concatenation — it compares, contrasts, and recommends. The brief is under 500 words with appendix links.
