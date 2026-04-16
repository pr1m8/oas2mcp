"""Structured output models for the catalog summarizer agent.

Purpose:
    Define agent-facing structured output models for summarizing an API catalog
    as a whole before introducing per-operation enhancement agents.

Design:
    - Use concise, typed structures that an agent can reliably fill.
    - Emphasize purpose, conceptual structure, domains, and data model before
      operational concerns like authentication or MCP surface design.
    - Keep these models specific to the summarizer workflow.

Examples:
    .. code-block:: python

        summary = CatalogSummary(
            catalog_name="Petstore",
            api_purpose="Manage pets, store orders, and users.",
            conceptual_overview="A demo REST API organized around pets, store operations, and users.",
            data_model_summary="The core schemas are Pet, User, Order, and ApiResponse.",
            data_flow_summary="The API supports both reads and mutations across core domains.",
            authentication_summary="OAuth2 and API key auth are present.",
            recommended_mcp_surface="Mostly tools with a few read-oriented resources.",
        )
"""

from __future__ import annotations

from pydantic import Field

from oas2mcp.models.normalized import NormalizedBaseModel


class CatalogTagSummary(NormalizedBaseModel):
    """Structured summary for one API tag or domain.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            tag_summary = CatalogTagSummary(
                tag_name="pet",
                description="Operations for pet records and media.",
                operation_count=8,
            )
    """

    tag_name: str
    description: str
    operation_count: int = 0
    read_operation_count: int = 0
    mutating_operation_count: int = 0
    notable_operations: list[str] = Field(default_factory=list)


class CatalogSummary(NormalizedBaseModel):
    """Structured overall summary of a normalized API catalog.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            summary = CatalogSummary(
                catalog_name="Petstore",
                api_purpose="Manage pets, orders, and users.",
                conceptual_overview="A demo REST API organized around three domains.",
                data_model_summary="The main schemas are Pet, User, Order, and ApiResponse.",
                data_flow_summary="Supports both reads and mutations across core domains.",
                authentication_summary="OAuth2 and API key auth are present.",
                recommended_mcp_surface="Use tools for actions and selected resources for reads.",
            )
    """

    catalog_name: str
    api_purpose: str
    conceptual_overview: str
    primary_domains: list[CatalogTagSummary] = Field(default_factory=list)
    data_model_summary: str
    data_flow_summary: str

    authentication_summary: str
    operational_notes: list[str] = Field(default_factory=list)

    recommended_mcp_surface: str
    suggested_tool_domains: list[str] = Field(default_factory=list)
    suggested_resource_domains: list[str] = Field(default_factory=list)

    notes: list[str] = Field(default_factory=list)
