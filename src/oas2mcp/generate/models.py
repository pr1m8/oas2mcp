"""Export models for enhanced OpenAPI and FastMCP generation."""

from __future__ import annotations

from pydantic import Field

from oas2mcp.agent.enhancer.models import OperationEnhancement
from oas2mcp.agent.summarizer.models import CatalogSummary
from oas2mcp.models.normalized import NormalizedBaseModel


class EnhancedCatalog(NormalizedBaseModel):
    """Collected enhanced catalog ready for export."""

    source_url: str
    catalog_name: str
    catalog_slug: str
    summary: CatalogSummary
    operations: list[OperationEnhancement] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
