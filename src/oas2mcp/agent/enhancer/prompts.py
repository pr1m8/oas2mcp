"""Prompt builders for the operation enhancer agent.

Purpose:
    Build prompt text for refining one normalized API operation into a cleaner
    MCP-friendly representation.

Design:
    - Keep prompt construction deterministic.
    - Use dynamic prompt middleware for runtime-aware instructions.
    - Keep the enhancer focused on one operation at a time.
    - Treat deterministic candidate values as hints, not final truth.
    - Make the required structured output explicit to reduce empty-object
      failures during orchestrated batch runs.

Examples:
    .. code-block:: python

        system_prompt = build_operation_enhancer_system_prompt()
        user_prompt = build_operation_enhancer_user_prompt(context)
"""

from __future__ import annotations

import json

from langchain.agents.middleware.types import dynamic_prompt

from oas2mcp.agent.enhancer.models import OperationEnhancementContext
from oas2mcp.agent.runtime import Oas2McpRuntimeContext


def build_operation_enhancer_runtime_instruction_lines(
    runtime: Oas2McpRuntimeContext,
) -> list[str]:
    """Build deterministic runtime-specific instructions for enhancer prompts."""
    lines: list[str] = []
    lines.append(f"Requested output style: {runtime.output_style}.")

    if runtime.include_mcp_recommendations:
        lines.append("Optimize the result for later MCP/OpenAPI export.")
    else:
        lines.append("Do not overemphasize MCP export details.")

    if runtime.include_risk_notes:
        lines.append(
            "Mention confirmation and auth considerations briefly when relevant."
        )
    else:
        lines.append("Keep confirmation and auth commentary minimal.")

    if runtime.project_name:
        lines.append(f"Project name: {runtime.project_name}")
    if runtime.user_goal:
        lines.append(f"User goal: {runtime.user_goal}")
    if runtime.notes:
        lines.append(f"Additional notes: {runtime.notes}")

    return lines


def build_operation_enhancer_system_prompt() -> str:
    """Build the base system prompt for the operation enhancer.

    Args:
        None.

    Returns:
        str: The system prompt.

    Raises:
        None.
    """
    return """You are an API operation enhancement assistant.

Your job is to refine one normalized API operation into a cleaner
MCP-friendly representation for later export into an enhanced OpenAPI/FastMCP
surface.

You must return a complete structured result for the current operation.

Required output fields:
- operation_key
- operation_slug
- final_kind
- title
- description

Additional optional fields:
- namespace
- tool_name
- resource_uri
- requires_confirmation
- auth_notes
- prompt_templates
- notes

Prioritize your enhancement in this order:
1. Improve the title and description.
2. Confirm or refine the final kind.
3. Improve tool or resource naming.
4. Add concise confirmation and auth guidance when needed.
5. Suggest only a small number of prompt templates if they add clear value.

Important:
- Focus only on the current operation.
- Treat deterministic candidate values as hints, not final truth.
- Stay grounded in the provided operation context.
- Do not invent new API capabilities.
- Do not redesign the entire API.
- Keep names concise and stable.
- Keep notes short and implementation-relevant.
- Never return an empty object.
"""


def build_operation_enhancer_dynamic_prompt():
    """Build dynamic prompt middleware for the enhancer.

    Args:
        None.

    Returns:
        The LangChain dynamic prompt middleware callable.

    Raises:
        None.
    """

    @dynamic_prompt
    def _dynamic_prompt(request) -> str:
        """Return the runtime-aware system prompt.

        Args:
            request: The LangChain middleware request object.

        Returns:
            str: A runtime-aware system prompt.

        Raises:
            None.
        """
        runtime = request.runtime.context

        base = build_operation_enhancer_system_prompt()
        if runtime is None or not isinstance(runtime, Oas2McpRuntimeContext):
            return base

        lines = build_operation_enhancer_runtime_instruction_lines(runtime)
        return base + "\nAdditional runtime instructions:\n- " + "\n- ".join(lines)

    return _dynamic_prompt


def build_operation_enhancer_user_prompt(
    context: OperationEnhancementContext,
) -> str:
    """Build the user prompt for one operation enhancement.

    Args:
        context: The operation enhancement context.

    Returns:
        str: The user prompt string.

    Raises:
        None.
    """
    serialized_context = json.dumps(
        context.model_dump(),
        indent=2,
        sort_keys=True,
    )

    return (
        "Enhance this one API operation for later MCP/OpenAPI export.\n\n"
        "Return a structured result aligned with the OperationEnhancement model.\n\n"
        "You must include at least these fields:\n"
        "- operation_key\n"
        "- operation_slug\n"
        "- final_kind\n"
        "- title\n"
        "- description\n\n"
        "If the operation is a tool, prefer a concise tool_name.\n"
        "If the operation is a resource, prefer a resource_uri.\n"
        "If confirmation or auth guidance matters, include it briefly.\n\n"
        "Operation enhancement context:\n"
        f"{serialized_context}"
    )
