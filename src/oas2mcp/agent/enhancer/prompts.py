"""Prompt builders for the operation enhancer agent."""

from __future__ import annotations

import json

from langchain.agents.middleware.types import dynamic_prompt

from oas2mcp.agent.enhancer.models import OperationEnhancementContext
from oas2mcp.agent.runtime import Oas2McpRuntimeContext


def build_operation_enhancer_system_prompt() -> str:
    """Build the base system prompt for the operation enhancer.

    Args:
        None.

    Returns:
        The system prompt string.
    """
    return """You are an API operation enhancement assistant.

Your job is to refine one normalized API operation into a cleaner MCP-friendly
representation.

Prioritize your enhancement in this order:
1. Improve the title and description.
2. Confirm or refine the operation kind.
3. Improve tool/resource naming.
4. Add concise auth and confirmation guidance.
5. Suggest only a small number of prompt templates if useful.

Important:
- Stay grounded in the provided operation context.
- Do not invent new API capabilities.
- Do not redesign the whole API.
- Focus only on the current operation.
"""


def build_operation_enhancer_dynamic_prompt():
    """Build dynamic prompt middleware for the enhancer."""

    @dynamic_prompt
    def _dynamic_prompt(request) -> str:
        runtime = request.runtime.context

        base = build_operation_enhancer_system_prompt()
        if runtime is None or not isinstance(runtime, Oas2McpRuntimeContext):
            return base

        lines: list[str] = []
        lines.append(f"Requested output style: {runtime.output_style}.")
        if runtime.include_mcp_recommendations:
            lines.append("Optimize the result for later MCP export.")
        if runtime.include_risk_notes:
            lines.append("Briefly mention confirmation or auth guidance when relevant.")
        if runtime.user_goal:
            lines.append(f"User goal: {runtime.user_goal}")

        return base + "\nAdditional runtime instructions:\n- " + "\n- ".join(lines)

    return _dynamic_prompt


def build_operation_enhancer_user_prompt(
    context: OperationEnhancementContext,
) -> str:
    """Build the user prompt for one operation enhancement.

    Args:
        context: The operation enhancement context.

    Returns:
        The user prompt string.
    """
    serialized_context = json.dumps(
        context.model_dump(),
        indent=2,
        sort_keys=True,
    )

    return (
        "Enhance this one API operation for later MCP/OpenAPI export.\n\n"
        "Return a structured result aligned with the OperationEnhancement model.\n\n"
        "Operation enhancement context:\n"
        f"{serialized_context}"
    )
