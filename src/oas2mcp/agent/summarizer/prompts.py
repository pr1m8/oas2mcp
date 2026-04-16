"""Prompt builders for the catalog summarizer agent.

Purpose:
    Build the prompt text used by the first catalog-level summarizer agent.

Design:
    - Keep prompt construction deterministic.
    - Separate the base system prompt from context serialization.
    - Align the prompt with the ``CatalogSummary`` structured output model.
    - Use LangChain v1 dynamic prompt middleware for runtime-aware system
      instructions.

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
    """Build the base system prompt for the catalog summarizer agent."""
    return """You are an API analysis assistant.

Your job is to summarize a normalized OpenAPI-derived API catalog for MCP planning.

You will receive compact structured context about:
- the API's identity and description
- domains and tags
- read, mutating, and destructive operation patterns
- security schemes
- schema reference rollups
- first-pass MCP candidate counts and examples

Produce a high-quality structured summary that:
- explains the API's overall purpose clearly
- identifies the main domains and what they do
- summarizes authentication and security implications
- summarizes read vs mutating vs destructive behavior
- recommends a high-level MCP surface
- suggests likely tool domains, resource domains, and prompt ideas
- highlights important risks and operational notes

Be concrete and concise.
Do not invent capabilities that are not supported by the provided context.
Prefer summarizing patterns over restating every operation individually.
"""


def build_catalog_summary_dynamic_prompt():
    """Build dynamic prompt middleware for the catalog summarizer."""

    @dynamic_prompt
    def _dynamic_prompt(request) -> str:
        """Return the runtime-aware system prompt."""
        runtime = request.runtime.context

        base = build_catalog_summary_system_prompt()
        if runtime is None or not isinstance(runtime, Oas2McpRuntimeContext):
            return base

        lines: list[str] = []
        lines.append(f"Requested output style: {runtime.output_style}.")
        if runtime.include_mcp_recommendations:
            lines.append("Include concrete MCP surface recommendations.")
        else:
            lines.append("Keep MCP recommendations minimal.")

        if runtime.include_risk_notes:
            lines.append("Include clear risk and confirmation guidance.")
        else:
            lines.append("Keep risk discussion brief.")

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
    """Build the user prompt for the catalog summarizer agent."""
    serialized_context = json.dumps(
        context.model_dump(),
        indent=2,
        sort_keys=True,
    )

    return (
        "Summarize this API catalog for MCP planning.\n\n"
        "Return a structured summary aligned with the CatalogSummary model.\n\n"
        "Catalog summary context:\n"
        f"{serialized_context}"
    )
