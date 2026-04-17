"""Prompt builders for the catalog surface planner agent."""

from __future__ import annotations

import json

from langchain.agents.middleware.types import dynamic_prompt

from oas2mcp.agent.runtime import Oas2McpRuntimeContext
from oas2mcp.agent.surface.models import CatalogSurfacePlanningContext


def build_catalog_surface_runtime_instruction_lines(
    runtime: Oas2McpRuntimeContext,
) -> list[str]:
    """Build deterministic runtime-specific instructions for surface planning."""
    lines: list[str] = [
        f"Requested output style: {runtime.output_style}.",
        "Prioritize a practical FastMCP surface that is easy to inspect and use.",
    ]

    if runtime.include_mcp_recommendations:
        lines.append(
            "Lean into MCP-specific ergonomics and shared prompt/resource design."
        )
    else:
        lines.append("Keep MCP-specific framing compact.")

    if runtime.project_name:
        lines.append(f"Project name: {runtime.project_name}")
    if runtime.user_goal:
        lines.append(f"User goal: {runtime.user_goal}")
    if runtime.notes:
        lines.append(f"Additional notes: {runtime.notes}")

    return lines


def build_catalog_surface_system_prompt() -> str:
    """Build the base system prompt for the catalog surface planner."""
    return """You are an MCP surface planning assistant.

Your job is to refine the shared, catalog-level FastMCP surface for an API that
has already been summarized and enhanced operation-by-operation.

You may improve:
1. The top-level FastMCP server instructions.
2. Shared catalog prompts that help a client navigate the API.
3. Shared catalog resources or resource templates that expose useful metadata.

You must not:
- Reclassify or rename individual operations.
- Duplicate one-operation prompts unless there is clear cross-operation value.
- Invent runtime handlers beyond the supported handler set.
- Turn the response into an implementation plan or risk memo.

Important constraints:
- Keep the shared surface compact and reusable.
- Preserve or improve the default prompts/resources instead of replacing them with worse variants.
- Only use supported resource handlers: `static`, `operation_metadata`, `namespace_operations`.
- Prefer prompts/resources that help with discovery, selection, and safe execution planning.
- Keep server instructions concise and specific.
- Keep all payloads JSON-serializable.
"""


def build_catalog_surface_dynamic_prompt():
    """Build dynamic prompt middleware for the catalog surface planner."""

    @dynamic_prompt
    def _dynamic_prompt(request) -> str:
        """Return the runtime-aware system prompt."""
        runtime = request.runtime.context

        base = build_catalog_surface_system_prompt()
        if runtime is None or not isinstance(runtime, Oas2McpRuntimeContext):
            return base

        lines = build_catalog_surface_runtime_instruction_lines(runtime)
        return base + "\nAdditional runtime instructions:\n- " + "\n- ".join(lines)

    return _dynamic_prompt


def build_catalog_surface_user_prompt(
    context: CatalogSurfacePlanningContext,
) -> str:
    """Build the user prompt for the catalog surface planner agent."""
    serialized_context = json.dumps(
        context.model_dump(),
        indent=2,
        sort_keys=True,
    )

    return (
        "Refine the shared catalog-level FastMCP surface for this enhanced API.\n\n"
        "Start from the deterministic defaults in the context, improve them where "
        "it adds real value, and keep the final surface executable by the current runtime.\n\n"
        "Return a structured plan aligned with the CatalogSurfacePlan model.\n\n"
        "Catalog surface planning context:\n"
        f"{serialized_context}"
    )
