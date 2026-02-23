"""Run logging for agent invocations.

Every invocation creates a run record in runs/{run-id}/ as specified
in Section 5 of the runtime spec.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class RunLogger:
    """Logs a single agent run to runs/{run-id}/."""

    def __init__(
        self,
        workspace: Path,
        agent_name: str,
        trigger: str,
        model: str,
    ):
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.run_id = f"{timestamp}-{agent_name}"
        self.run_dir = workspace / "runs" / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.tool_calls_dir = self.run_dir / "tool-calls"
        self.tool_calls_dir.mkdir(exist_ok=True)
        self.tool_call_count = 0

        # Write meta.yaml
        meta = {
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "trigger": trigger,
            "model": model,
            "run_id": self.run_id,
        }
        (self.run_dir / "meta.yaml").write_text(yaml.dump(meta, default_flow_style=False))

        # Initialize conversation log
        self.conversation_path = self.run_dir / "conversation.jsonl"

    def log_context(self, system_prompt: str, messages: list[dict]) -> None:
        """Log the full assembled context."""
        context_parts = [f"# System Prompt\n\n{system_prompt}\n"]
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if isinstance(content, str):
                context_parts.append(f"# {role.title()}\n\n{content}\n")
            else:
                context_parts.append(f"# {role.title()}\n\n{json.dumps(content, indent=2)}\n")

        (self.run_dir / "context.md").write_text("\n---\n\n".join(context_parts))

    def log_event(self, event_type: str, data: Any) -> None:
        """Log a generic event to the conversation log."""
        entry = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }
        with open(self.conversation_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def log_api_call(self, request: Any, response: Any) -> None:
        """Log an API request/response pair."""
        entry = {
            "type": "api_call",
            "timestamp": datetime.now().isoformat(),
            "stop_reason": getattr(response, "stop_reason", None),
            "usage": {
                "input_tokens": getattr(getattr(response, "usage", None), "input_tokens", 0),
                "output_tokens": getattr(getattr(response, "usage", None), "output_tokens", 0),
            },
        }
        with open(self.conversation_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def log_tool_call(self, tool_use: dict, result: str) -> None:
        """Log a tool call and its result."""
        self.tool_call_count += 1
        idx = f"{self.tool_call_count:03d}"

        # Log to tool-calls/ directory (untruncated)
        call_file = self.tool_calls_dir / f"{idx}-{tool_use['name']}.json"
        call_data = {
            "tool": tool_use["name"],
            "input": tool_use["input"],
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }
        call_file.write_text(json.dumps(call_data, indent=2))

        # Log to conversation
        entry = {
            "type": "tool_call",
            "timestamp": datetime.now().isoformat(),
            "tool": tool_use["name"],
            "input_summary": str(tool_use["input"])[:200],
            "result_length": len(result),
        }
        with open(self.conversation_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def log_outcome(self, text: str) -> None:
        """Log the final outcome of the run."""
        (self.run_dir / "outcome.md").write_text(
            f"# Outcome\n\n{text}\n" if text else "# Outcome\n\nNO_REPLY\n"
        )
