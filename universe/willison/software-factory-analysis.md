# How StrongDM's AI team build serious software without even looking at the code

**By Simon Willison | 7th February 2026**

Source: https://simonwillison.net/2026/Feb/7/software-factory/

StrongDM's AI team has developed a "Software Factory" approach where coding agents write, test, and deploy software without human code review. The team established two foundational rules:

- "Code **must not be** written by humans"
- "Code **must not be** reviewed by humans"

## The Challenge of Unreviewed Code

The critical question: how to ensure unreviewed LLM-generated code actually works? The team was inspired by November 2025's inflection point when Claude Opus 4.5 and GPT 5.2 demonstrated significantly improved reliability for agentic coding tasks.

StrongDM's earlier catalyst came in October 2024 with Claude 3.5's second revision, when "long-horizon agentic coding workflows began to compound correctness rather than error."

## The Solution: Scenarios and Digital Twin Universe

Rather than traditional test suites, StrongDM uses **scenarios**—end-to-end user stories stored outside the codebase as "holdout sets," similar to model training validation data. They introduced **satisfaction** as a probabilistic metric: the fraction of observed trajectories through scenarios likely satisfying users.

The breakthrough innovation is the **Digital Twin Universe (DTU)**—behavioral clones of third-party services their software depends on. They created replicas of Okta, Jira, Slack, Google Docs, Google Drive, and Google Sheets, replicating APIs, edge cases, and observable behaviors.

## Building the Clones

The approach involved dumping full public API documentation into their agent harness, which built imitations as self-contained binaries. A key prompting strategy: "Use the top popular publicly available reference SDK client libraries as compatibility targets, with the goal always being 100% compatibility."

This allowed agents to validate at unprecedented volumes without hitting rate limits, triggering abuse detection, or incurring API costs. The DTU enabled thousands of scenario tests per hour against live-like systems.

## Additional Techniques

StrongDM introduced specialized methodologies:

- **Gene Transfusion**: extracting patterns from existing systems for reuse elsewhere
- **Semports**: directly porting code between programming languages
- **Pyramid Summaries**: multi-level summaries allowing agents to scan briefly or zoom into details as needed

## Open Releases

The team released:

1. **Attractor**: Their non-interactive coding agent, published as markdown specs rather than code—intended to be fed into coding agents
2. **CXDB**: A 16,000-line Rust, 9,500-line Go, and 6,700-line TypeScript "AI Context Store" for storing conversation histories and tool outputs in an immutable DAG

## The Cost Question

One significant caveat: the team mentioned spending "at least $1,000 on tokens today per human engineer." This monthly cost of approximately $20,000 per engineer raises questions about economic feasibility and sustainability for most organizations.

## The Broader Implication

This represents a fundamental shift in software development: engineers transition from writing code to building and monitoring systems that generate code. It challenges conventional assumptions about code review, testing, and quality assurance while raising important questions about whether these patterns can operate sustainably at lower cost.

---

## Key Insights for the Factory

(These are the principles this factory draws from Willison's analysis)

1. **NLSpecs as the unit of work** — The Attractor repo contains zero code. Just three markdown files totaling ~6,000-7,000 lines of specification. The specs ARE the product.

2. **Scenario holdouts** — End-to-end user stories stored outside the codebase, hidden from building agents. Equivalent to ML holdout sets. Prevents reward hacking.

3. **Satisfaction over pass/fail** — "Of 10 users who wanted this, how many would be satisfied?" is a better metric than boolean test results.

4. **Digital Twin Universe** — Behavioral clones of dependencies. The factory's `universe/` directory serves an analogous role: reference material that grounds agent decisions.

5. **Jay Taylor's insight** — The DTU doesn't need perfect fidelity, just enough to match what real SDK clients expect. Use popular SDK client libraries as compatibility targets.
