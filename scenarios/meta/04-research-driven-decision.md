# Scenario 4: Research-Driven Decision

**Title:** Researcher prevents a bad architectural choice

**Story:** Spec is about to spec a project using an approach that has known problems. Researcher catches it.

**Expected trajectory:**

The developer writes an intent for a real-time notification system. Spec starts drafting and writes a research request: "What's the best approach for real-time notifications in a Node.js server? WebSockets vs SSE vs polling?"

Researcher evaluates all three. The brief recommends SSE for this use case (one-way server→client, simpler reconnection, works through proxies) but notes that if the spec later requires bidirectional communication, WebSocket is better. Confidence: high.

Spec reads the brief and writes the NLSpec with an informed constraint: "The system uses Server-Sent Events for notification delivery" with a note in the Out of Scope section: "Bidirectional real-time communication is out of scope. If needed later, re-evaluate with WebSocket approach per research brief."

**Satisfaction criteria:** The spec contains an informed architectural decision with clear reasoning, not a guess. The Out of Scope section prevents gold-plating. If the developer later needs bidirectional, the research brief is archived and findable.
