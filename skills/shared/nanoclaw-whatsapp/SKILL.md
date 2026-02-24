---
name: nanoclaw-whatsapp
description: Send WhatsApp messages through NanoClaw's IPC. Use when an agent needs to notify the human via WhatsApp about completed work, failures, decisions needed, or status updates.
---

## How It Works

NanoClaw watches a filesystem directory for JSON message files. Write a `.json` file to NanoClaw's IPC messages directory, and NanoClaw picks it up within 1 second and sends it via WhatsApp.

## IPC Directory

Write to the `notifications/` directory in the Factory workspace. This is a symlink to NanoClaw's IPC:

```
notifications/
```

## Message Format

Write a JSON file with a unique name (timestamp + random suffix recommended):

```json
{
  "type": "message",
  "chatJid": "855718665780@s.whatsapp.net",
  "text": "Your message content here"
}
```

- `type` must be `"message"`
- `chatJid` is the WhatsApp chat to send to (the self-chat JID above is the human's main channel)
- `text` is the message body (plain text, WhatsApp formatting supported: *bold*, _italic_, ~strikethrough~, ```code```)

## File Naming

Use this pattern to avoid collisions:

```
{timestamp}-{agent}-{brief}.json
```

Example: `1740470400000-verifier-spec-passed.json`

## When to Notify

Use judgement. Not every action needs a WhatsApp message. Good reasons to notify:

- **Verification complete** — spec passed or failed (Verifier)
- **Decision needed** — ambiguity blocking progress (Spec, Builder)
- **Build complete** — significant deliverable ready for review (Builder)
- **Health alert** — deployed project unhealthy twice in a row (Operator)
- **Research brief ready** — findings that change project direction (Researcher)

Do NOT notify for routine heartbeat activity, daily log entries, or minor internal state changes.

## Message Style

Keep messages brief and actionable. The human reads these on a phone.

Good:
```
Spec "multi-cli-backend-support" verified. 4/4 scenarios pass. Ready for deployment.
```

Bad:
```
Hello! I wanted to let you know that I have completed the verification process for the specification titled "multi-cli-backend-support". The verification involved running 4 scenarios, all of which passed successfully. The work is now ready for the next stage of the pipeline.
```

## Example

```bash
cat > notifications/$(date +%s%3N)-operator-health.json << 'EOF'
{
  "type": "message",
  "chatJid": "855718665780@s.whatsapp.net",
  "text": "Health alert: git-commit-viewer API returning 503 for 2 consecutive checks. Maintenance task created."
}
EOF
```

## Access Control

Only agents with write access to the NanoClaw IPC path can send messages. The NanoClaw IPC watcher validates that messages originate from the `main` group directory (which has unrestricted send permissions).
