"""Deterministic context builders for the catalog surface planner agent."""

from __future__ import annotations

from oas2mcp.agent.surface.models import (
    CatalogSurfaceOperationContext,
    CatalogSurfacePlanningContext,
    CatalogSurfacePromptPlan,
    CatalogSurfaceResourcePlan,
)
from oas2mcp.generate.models import EnhancedCatalog
from oas2mcp.generate.surface_defaults import (
    build_default_catalog_prompt_definitions,
    build_default_catalog_resource_definitions,
    build_default_server_instructions,
)


def build_catalog_surface_planning_context(
    enhanced_catalog: EnhancedCatalog,
) -> CatalogSurfacePlanningContext:
    """Build deterministic context for catalog-level FastMCP surface planning."""
    default_prompts = [
        CatalogSurfacePromptPlan.model_validate(prompt.model_dump())
        for prompt in build_default_catalog_prompt_definitions(enhanced_catalog)
    ]
    default_resources = [
        CatalogSurfaceResourcePlan.model_validate(resource.model_dump())
        for resource in build_default_catalog_resource_definitions(enhanced_catalog)
    ]

    return CatalogSurfacePlanningContext(
        catalog_name=enhanced_catalog.catalog_name,
        catalog_slug=enhanced_catalog.catalog_slug,
        catalog_version=enhanced_catalog.catalog_version,
        source_uri=enhanced_catalog.source_url,
        api_purpose=enhanced_catalog.summary.api_purpose,
        conceptual_overview=enhanced_catalog.summary.conceptual_overview,
        authentication_summary=enhanced_catalog.summary.authentication_summary,
        recommended_mcp_surface=enhanced_catalog.summary.recommended_mcp_surface,
        primary_domains=[
            domain.tag_name for domain in enhanced_catalog.summary.primary_domains
        ],
        suggested_tool_domains=enhanced_catalog.summary.suggested_tool_domains,
        suggested_resource_domains=enhanced_catalog.summary.suggested_resource_domains,
        catalog_notes=[
            *enhanced_catalog.summary.notes,
            *enhanced_catalog.summary.operational_notes,
            *enhanced_catalog.notes,
        ],
        operations=[
            CatalogSurfaceOperationContext(
                operation_slug=operation.operation_slug,
                operation_id=operation.operation_id,
                final_kind=operation.final_kind,
                namespace=operation.namespace,
                title=operation.title,
                description=operation.description,
                tool_name=operation.tool_name,
                resource_uri=operation.resource_uri,
                requires_confirmation=operation.requires_confirmation,
                auth_notes=operation.auth_notes,
                prompt_template_names=[
                    prompt_template.name
                    for prompt_template in operation.prompt_templates
                ],
            )
            for operation in enhanced_catalog.operations
        ],
        default_server_instructions=build_default_server_instructions(enhanced_catalog),
        default_catalog_prompts=default_prompts,
        default_catalog_resources=default_resources,
    )
