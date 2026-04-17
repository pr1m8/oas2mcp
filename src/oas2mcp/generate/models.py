"""Export models for enhanced OpenAPI and FastMCP generation."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from oas2mcp.agent.enhancer.models import OperationEnhancement
from oas2mcp.agent.summarizer.models import CatalogSummary
from oas2mcp.agent.surface.models import CatalogSurfacePlan
from oas2mcp.models.normalized import NormalizedBaseModel


class CatalogPromptDefinition(NormalizedBaseModel):
    """Prompt metadata exported for FastMCP registration."""

    name: str
    title: str
    description: str
    arguments: list[str] = Field(default_factory=list)
    template: str
    version: str | None = None
    tags: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class CatalogResourceDefinition(NormalizedBaseModel):
    """Resource metadata exported for FastMCP registration."""

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


class EnhancedCatalog(NormalizedBaseModel):
    """Collected enhanced catalog ready for export."""

    source_url: str
    catalog_name: str
    catalog_slug: str
    catalog_version: str | None = None
    summary: CatalogSummary
    operations: list[OperationEnhancement] = Field(default_factory=list)
    surface_plan: CatalogSurfacePlan | None = None
    notes: list[str] = Field(default_factory=list)
