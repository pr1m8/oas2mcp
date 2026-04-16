"""Prompt builders for the catalog summarizer agent.

Purpose:
    Build the prompt text used by the catalog-level summarizer agent.

Design:
    - Keep prompt construction deterministic.
    - Separate the base system prompt from context serialization.
    - Align the prompt with the ``CatalogSummary`` structured output model.
    - Use LangChain v1 dynamic prompt middleware for runtime-aware system
      instructions.
    - Prioritize conceptual understanding of the API before operational or
      implementation detail.

Examples:
    .. code-block:: python

        system_prompt = build_catalog_summary_system_prompt()
        user_prompt = build_catalog_summary_user_prompt(context)
"""

from __future__ import annotations

import json

from langchain.agents.middleware.types import dynamic_prompt

from oas2mcp.agent.runtime import Oas2McpRuntimeContext
from oas2mcp.agent.summarizer.context import CatalogSummaryContext


def build_catalog_summary_system_prompt() -> str:
    """Build the base system prompt for the catalog summarizer agent.

    Args:
        None.

    Returns:
        The system prompt string.

    Raises:
        None.

    Examples:
        .. code-block:: python

            prompt = build_catalog_summary_system_prompt()
    """
    return """You are an API analysis assistant.

Your job is to summarize a normalized OpenAPI-derived API catalog at a high level.

Prioritize your summary in this order:
1. Explain what the API is for overall.
2. Explain its major domains and how they relate to each other.
3. Explain its main data model and request/response patterns.
4. Briefly summarize authentication requirements and notable operational caveats.
5. Give only a short, high-level MCP framing.

Your summary must be grounded in the provided context and aligned with the CatalogSummary schema.

Important:
- Focus on the shape, purpose, and conceptual structure of the API.
- Do not let operational caveats dominate the summary.
- Do not turn the response into a detailed implementation plan.
- Do not provide endpoint-by-endpoint MCP mappings.
- Do not generate prompt ideas, workflow recipes, or deployment instructions.
- Do not enumerate every operation unless needed to explain a domain.
- Prefer conceptual grouping over operational detail.
- Keep suggested tool/resource domains short and broad.
- Keep the MCP framing concise and high-level.
- Keep notes short and conceptual.
- Do not invent capabilities or deployment assumptions not supported by the provided context.
"""


def build_catalog_summary_dynamic_prompt():
    """Build dynamic prompt middleware for the catalog summarizer.

    Returns:
        The LangChain dynamic prompt middleware callable.

    Raises:
        None.

    Examples:
        .. code-block:: python

            middleware = build_catalog_summary_dynamic_prompt()
    """

    @dynamic_prompt
    def _dynamic_prompt(request) -> str:
        """Return the runtime-aware system prompt.

        Args:
            request: The LangChain middleware request object.

        Returns:
            The runtime-aware system prompt.

        Raises:
            None.
        """
        runtime = request.runtime.context

        base = build_catalog_summary_system_prompt()
        if runtime is None or not isinstance(runtime, Oas2McpRuntimeContext):
            return base

        lines: list[str] = []
        lines.append(f"Requested output style: {runtime.output_style}.")
        lines.append(
            "Focus first on conceptual understanding, then on light implementation implications."
        )

        if runtime.include_mcp_recommendations:
            lines.append(
                "Include brief high-level MCP framing, but keep it clearly secondary to understanding the API."
            )
        else:
            lines.append("Do not emphasize MCP framing.")

        if runtime.include_risk_notes:
            lines.append(
                "You may mention notable operational caveats briefly, but do not let them dominate the summary."
            )
        else:
            lines.append("Keep operational caveats minimal.")

        if runtime.project_name:
            lines.append(f"Project name: {runtime.project_name}")
        if runtime.user_goal:
            lines.append(f"User goal: {runtime.user_goal}")
        if runtime.notes:
            lines.append(f"Additional notes: {runtime.notes}")

        return base + "\nAdditional runtime instructions:\n- " + "\n- ".join(lines)

    return _dynamic_prompt


def build_catalog_summary_user_prompt(
    context: CatalogSummaryContext,
) -> str:
    """Build the user prompt for the catalog summarizer agent.

    Args:
        context: The structured summarizer context.

    Returns:
        The user prompt string.

    Raises:
        None.

    Examples:
        .. code-block:: python

            user_prompt = build_catalog_summary_user_prompt(context)
    """
    serialized_context = json.dumps(
        context.model_dump(),
        indent=2,
        sort_keys=True,
    )

    return (
        "Summarize this API catalog at a high level for later MCP-oriented design work.\n\n"
        "Focus primarily on the API's purpose, conceptual structure, domains, data model, and data flow.\n"
        "Treat authentication, operational caveats, and MCP implications as secondary supporting analysis.\n\n"
        "Return a structured summary aligned with the CatalogSummary model.\n\n"
        "Catalog summary context:\n"
        f"{serialized_context}"
    )
