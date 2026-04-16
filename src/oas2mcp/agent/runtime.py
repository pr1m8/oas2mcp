"""Shared runtime context for ``oas2mcp`` agents.

Purpose:
    Define the runtime context passed into agent executions.

Design:
    - Keep runtime context separate from normalized API models.
    - Use runtime context for per-invocation settings and user intent.
    - Keep the shape small and easy to evolve.

Examples:
    .. code-block:: python

        runtime_context = Oas2McpRuntimeContext(
            source_uri="https://example.com/openapi.json",
            user_goal="Summarize this API for MCP planning.",
        )
"""

from __future__ import annotations

from pydantic import Field

from oas2mcp.models.normalized import NormalizedBaseModel


class Oas2McpRuntimeContext(NormalizedBaseModel):
    """Runtime context shared across ``oas2mcp`` agent workflows.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            runtime_context = Oas2McpRuntimeContext(
                source_uri="https://example.com/openapi.json",
                output_style="compact",
            )
    """

    source_uri: str
    output_style: str = "compact"
    include_mcp_recommendations: bool = True
    include_risk_notes: bool = True
    project_name: str | None = None
    user_goal: str | None = None
    notes: list[str] = Field(default_factory=list)
