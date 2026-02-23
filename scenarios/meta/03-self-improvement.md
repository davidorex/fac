# Scenario 3: The Self-Improvement Loop

**Title:** A failure becomes a learning becomes a skill

**Story:** Builder encounters a Python packaging issue that wastes 3 retries. The pattern is recognized and a skill is proposed.

**Expected trajectory:**

Builder tries to implement a project that requires a `pyproject.toml` with package data. The first attempt uses an outdated `setup.py` pattern. The second attempt gets the TOML syntax wrong. The third attempt works but wastes significant token budget.

Builder writes a learning to `learnings/failures/` describing the issue. Librarian, on its nightly review, notices this is the second Python packaging failure in a week. Librarian writes a new skill to `skills/proposed/python-packaging/SKILL.md` that documents the correct `pyproject.toml` patterns. On the next nightly review, Librarian promotes it to `skills/shared/`.

Next time Builder starts a Python project, the `python-packaging` skill appears in its available skills list. It loads the skill and scaffolds the project correctly on the first attempt.

**Satisfaction criteria:** The whole loop completes without human intervention. The skill is accurate and concise. Builder's next Python project scaffolds cleanly.
