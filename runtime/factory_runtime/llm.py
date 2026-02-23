"""LLM client for invoking agents via the Anthropic API.

Handles the agent loop: send context, process tool calls, repeat
until the agent produces a final text response.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import anthropic

from .config import AgentConfig, FactoryConfig
from .context import assemble_context, build_context_bar, estimate_tokens, MODEL_CONTEXT_WINDOWS, CHARS_PER_TOKEN
from .tools import execute_tool, get_tool_definitions
from .run_log import RunLogger


def run_agent(
    config: FactoryConfig,
    agent_config: AgentConfig,
    task_content: str | None = None,
    message: str | None = None,
    is_heartbeat: bool = False,
    run_logger: RunLogger | None = None,
) -> str:
    """Run a single agent invocation through the full agent loop.

    Returns the agent's final text response.
    """
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY from env

    system_prompt, messages, context_bar = assemble_context(
        config, agent_config, task_content, message, is_heartbeat,
    )

    tools = get_tool_definitions(agent_config)

    if run_logger:
        run_logger.log_context(system_prompt, messages)
        run_logger.log_event("context_bar", context_bar)

    # Map model names to API model IDs
    model_map = {
        "claude-opus-4-6": "claude-opus-4-6",
        "claude-sonnet-4-5": "claude-sonnet-4-5-20250514",
        "claude-sonnet-4-6": "claude-sonnet-4-6",
        "claude-haiku-4-5": "claude-haiku-4-5-20251001",
    }
    model_id = model_map.get(agent_config.model, agent_config.model)

    max_iterations = 50  # safety cap
    iteration = 0
    final_text = ""

    while iteration < max_iterations:
        iteration += 1

        # Check context budget and inject warnings
        all_text = system_prompt + json.dumps(messages)
        token_est = estimate_tokens(all_text)
        max_window = MODEL_CONTEXT_WINDOWS.get(agent_config.model, 200_000)
        pct = (token_est / max_window) * 100

        if pct >= 90:
            messages.append({
                "role": "user",
                "content": (
                    f"🛑 Context at {pct:.0f}%. Write critical state to disk NOW. "
                    "Next turn will trigger compaction."
                ),
            })
        elif pct >= 70:
            messages.append({
                "role": "user",
                "content": (
                    f"⚠ Context at {pct:.0f}%. Consider writing durable state to "
                    "memory/daily log and starting a fresh session."
                ),
            })

        # Call the API
        response = client.messages.create(
            model=model_id,
            max_tokens=16384,
            system=system_prompt,
            messages=messages,
            tools=tools if tools else anthropic.NOT_GIVEN,
        )

        if run_logger:
            run_logger.log_api_call(messages[-1] if messages else {}, response)

        # Process response content blocks
        assistant_content = response.content
        text_parts: list[str] = []
        tool_uses: list[dict] = []

        for block in assistant_content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

        # Append assistant message to conversation
        messages.append({"role": "assistant", "content": assistant_content})

        if text_parts:
            final_text = "\n".join(text_parts)

        # If no tool calls, the agent is done
        if not tool_uses:
            break

        # Execute tool calls and build results
        tool_results = []
        for tool_use in tool_uses:
            result = execute_tool(
                tool_use["name"],
                tool_use["input"],
                agent_config,
                config,
            )

            if run_logger:
                run_logger.log_tool_call(tool_use, result)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use["id"],
                "content": result,
            })

        # Add tool results to conversation
        messages.append({"role": "user", "content": tool_results})

        # Check stop reason
        if response.stop_reason == "end_turn":
            break

    if run_logger:
        run_logger.log_outcome(final_text)

    return final_text
