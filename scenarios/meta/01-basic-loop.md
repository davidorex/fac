# Scenario 1: The Basic Loop

**Title:** First project from intent to verified code

**Story:** A developer writes a two-sentence intent into `specs/inbox/cold-emailer.md`: "A Python CLI tool that takes a CSV of contacts and a template file, renders personalized emails, and outputs them as individual .eml files. It should validate email addresses and skip malformed rows with a warning."

**Expected trajectory:**

The developer runs `factory run spec --task specs/inbox/cold-emailer.md`. Spec reads the intent and writes a research request: "What's the standard approach for .eml file generation in Python? What validation library is best for email addresses?" Researcher picks it up (on its next heartbeat or a manual run), evaluates `email.message` stdlib vs `flanker` vs regex, and writes a brief recommending `email.message` + a simple regex validator with a note about RFC 5322 edge cases.

Spec reads the brief and writes a full NLSpec to `specs/drafting/cold-emailer.md`, then moves it to `specs/ready/`. The spec includes behavioral requirements for template rendering, CSV parsing, validation, .eml output format, error handling for malformed rows, and CLI interface (`cold-emailer --contacts contacts.csv --template template.txt --output ./emails/`).

Builder picks up the spec on its next heartbeat, implements the tool in `projects/cold-emailer/`, writes tests, runs them until green, writes builder-notes, and moves the task to `tasks/review/`.

Verifier reads the spec, reads the code, reads this scenario (which describes a user with 500 contacts, 3 of which have malformed emails, who expects 497 .eml files and a warning log), and scores satisfaction.

**Satisfaction criteria:** A developer who wanted exactly what the intent described would be satisfied if: the tool works on first run with valid inputs, malformed rows produce clear warnings (not crashes), the .eml files are valid and openable in a mail client, and the CLI help text is self-explanatory.
