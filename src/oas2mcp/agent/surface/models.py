"""Structured models for the catalog surface planner agent.

Purpose:
    Define the deterministic input and structured output models used by the
    catalog-level surface planner. This workflow refines shared FastMCP-facing
    server instructions, prompts, and resources after per-operation enhancement.

Design:
    - Keep these models specific to catalog-level surface planning.
    - Separate deterministic planning context from LLM-produced surface output.
    - Preserve a stable, inspectable shape for later export and bootstrapping.
    - Constrain resource planning to handlers supported by the runtime layer.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from oas2mcp.models.mcp import McpCandidateKind
from oas2mcp.models.normalized import NormalizedBaseModel


class CatalogSurfacePromptPlan(NormalizedBaseModel):
    """Catalog-level prompt definition proposed by the surface planner."""

    name: str
    title: str
    description: str
    arguments: list[str] = Field(default_factory=list)
    template: str
    version: str | None = None
    tags: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class CatalogSurfaceResourcePlan(NormalizedBaseModel):
    """Catalog-level resource definition proposed by the surface planner."""

    kind: Literal["resource", "resource_template"]
    uri: str
    name: str
    title: str
    description: str
    mime_type: str = "application/json"
    handler: Literal["static", "operation_metadata", "namespace_operations"] = "static"
    arguments: list[str] = Field(default_factory=list)
    payload: Any | None = None
    version: str | None = None
    tags: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
    annotations: dict[str, Any] = Field(default_factory=dict)


class CatalogSurfaceOperationContext(NormalizedBaseModel):
    """Compact operation summary used by the catalog surface planner."""

    operation_slug: str
    operation_id: str | None = None
    final_kind: McpCandidateKind
    namespace: str | None = None
    title: str
    description: str
    tool_name: str | None = None
    resource_uri: str | None = None
    requires_confirmation: bool = False
    auth_notes: str | None = None
    prompt_template_names: list[str] = Field(default_factory=list)


class CatalogSurfacePlanningContext(NormalizedBaseModel):
    """Deterministic context passed into the catalog surface planner agent."""

    catalog_name: str
    catalog_slug: str
    catalog_version: str | None = None
    source_uri: str

    api_purpose: str
    conceptual_overview: str
    authentication_summary: str
    recommended_mcp_surface: str
    primary_domains: list[str] = Field(default_factory=list)
    suggested_tool_domains: list[str] = Field(default_factory=list)
    suggested_resource_domains: list[str] = Field(default_factory=list)
    catalog_notes: list[str] = Field(default_factory=list)

    operations: list[CatalogSurfaceOperationContext] = Field(default_factory=list)

    default_server_instructions: str
    default_catalog_prompts: list[CatalogSurfacePromptPlan] = Field(
        default_factory=list
    )
    default_catalog_resources: list[CatalogSurfaceResourcePlan] = Field(
        default_factory=list
    )


class CatalogSurfacePlan(NormalizedBaseModel):
    """Structured catalog-level surface plan produced by the planner agent."""

    server_instructions: str
    catalog_prompts: list[CatalogSurfacePromptPlan] = Field(default_factory=list)
    catalog_resources: list[CatalogSurfaceResourcePlan] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
