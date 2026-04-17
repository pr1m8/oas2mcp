"""Deterministic default FastMCP surface builders.

Purpose:
    Centralize the catalog-level FastMCP defaults used both by export and by
    the catalog surface planner agent context.
"""

from __future__ import annotations

from typing import Any

from oas2mcp.generate.models import (
    CatalogPromptDefinition,
    CatalogResourceDefinition,
    EnhancedCatalog,
)


def build_default_server_instructions(enhanced_catalog: EnhancedCatalog) -> str:
    """Build concise default FastMCP server instructions from the catalog."""
    domain_names = ", ".join(
        domain.tag_name for domain in enhanced_catalog.summary.primary_domains
    )
    instruction_lines = [
        f"API purpose: {enhanced_catalog.summary.api_purpose}",
        (
            "Primary domains: "
            + (domain_names if domain_names else "No major domains were identified.")
        ),
    ]

    if enhanced_catalog.summary.recommended_mcp_surface:
        instruction_lines.append(
            f"Recommended MCP surface: {enhanced_catalog.summary.recommended_mcp_surface}"
        )
    if enhanced_catalog.summary.authentication_summary:
        instruction_lines.append(
            f"Authentication summary: {enhanced_catalog.summary.authentication_summary}"
        )

    return "\n".join(instruction_lines)


def build_default_catalog_prompt_definitions(
    enhanced_catalog: EnhancedCatalog,
) -> list[CatalogPromptDefinition]:
    """Build deterministic catalog-level prompt definitions."""
    operations_listing = "\n".join(
        f"- {operation.operation_slug}: [{operation.final_kind}] "
        f"{operation.title} — {operation.description}"
        for operation in enhanced_catalog.operations
    )
    namespaces_listing = "\n".join(
        f"- {namespace}: "
        + ", ".join(
            operation.operation_slug
            for operation in enhanced_catalog.operations
            if operation.namespace == namespace
        )
        for namespace in _list_namespaces(enhanced_catalog)
    )

    version = enhanced_catalog.catalog_version
    base_meta = {
        "generated_by": "oas2mcp",
        "catalog_slug": enhanced_catalog.catalog_slug,
    }
    return [
        CatalogPromptDefinition(
            name="catalog_overview",
            title="Catalog overview",
            description="Explain the API catalog and how its major domains fit together.",
            arguments=["user_goal"],
            template=(
                f"API catalog: {enhanced_catalog.catalog_name}\n"
                f"Purpose: {enhanced_catalog.summary.api_purpose}\n"
                f"Conceptual overview: {enhanced_catalog.summary.conceptual_overview}\n"
                f"Recommended MCP surface: {enhanced_catalog.summary.recommended_mcp_surface}\n"
                "User goal: {user_goal}\n\n"
                "Explain which API areas look most relevant and why."
            ),
            version=version,
            tags=["catalog", "overview"],
            meta=base_meta,
        ),
        CatalogPromptDefinition(
            name="select_operation",
            title="Select operation",
            description="Choose the most relevant exported operation for a user goal.",
            arguments=["user_goal"],
            template=(
                f"API catalog: {enhanced_catalog.catalog_name}\n"
                "Available operations:\n"
                f"{operations_listing}\n\n"
                "User goal: {user_goal}\n\n"
                "Choose the best operation slug, explain why it fits, and mention "
                "any auth or confirmation requirements."
            ),
            version=version,
            tags=["catalog", "planning"],
            meta=base_meta,
        ),
        CatalogPromptDefinition(
            name="plan_operation",
            title="Plan operation use",
            description="Plan how to use one exported operation for a specific goal.",
            arguments=["operation_slug", "user_goal"],
            template=(
                f"API catalog: {enhanced_catalog.catalog_name}\n"
                "Operation slug: {operation_slug}\n"
                "User goal: {user_goal}\n\n"
                f"Use the resource template "
                f"`oas2mcp://{enhanced_catalog.catalog_slug}/operations/{{operation_slug}}` "
                "to inspect the operation metadata first, then describe the safest "
                "execution plan."
            ),
            version=version,
            tags=["catalog", "operation"],
            meta=base_meta,
        ),
        CatalogPromptDefinition(
            name="browse_namespace",
            title="Browse namespace",
            description="Browse operations grouped under one namespace or domain.",
            arguments=["namespace", "user_goal"],
            template=(
                f"API catalog: {enhanced_catalog.catalog_name}\n"
                "Namespaces:\n"
                f"{namespaces_listing or '- none'}\n\n"
                "Namespace: {namespace}\n"
                "User goal: {user_goal}\n\n"
                f"Use the resource template "
                f"`oas2mcp://{enhanced_catalog.catalog_slug}/namespaces/{{namespace}}/operations` "
                "to inspect the namespace and explain the most relevant operations."
            ),
            version=version,
            tags=["catalog", "namespace"],
            meta=base_meta,
        ),
        CatalogPromptDefinition(
            name="compare_operations",
            title="Compare operations",
            description="Compare multiple exported operations for one user goal.",
            arguments=["operation_slugs", "user_goal"],
            template=(
                f"API catalog: {enhanced_catalog.catalog_name}\n"
                "Operation slugs to compare: {operation_slugs}\n"
                "User goal: {user_goal}\n\n"
                "Compare the listed operations by purpose, safety, confirmation, "
                "and when each one should be used."
            ),
            version=version,
            tags=["catalog", "comparison"],
            meta=base_meta,
        ),
    ]


def build_default_catalog_resource_definitions(
    enhanced_catalog: EnhancedCatalog,
) -> list[CatalogResourceDefinition]:
    """Build deterministic catalog-level resources and resource templates."""
    version = enhanced_catalog.catalog_version
    base_meta = {
        "generated_by": "oas2mcp",
        "catalog_slug": enhanced_catalog.catalog_slug,
    }
    catalog_summary_payload = {
        "catalog_name": enhanced_catalog.catalog_name,
        "catalog_slug": enhanced_catalog.catalog_slug,
        "catalog_version": enhanced_catalog.catalog_version,
        "source_uri": enhanced_catalog.source_url,
        "summary": enhanced_catalog.summary.model_dump(),
        "operations": [
            {
                "operation_slug": operation.operation_slug,
                "operation_id": operation.operation_id,
                "final_kind": operation.final_kind,
                "namespace": operation.namespace,
                "title": operation.title,
                "description": operation.description,
                "tool_name": operation.tool_name,
                "resource_uri": operation.resource_uri,
            }
            for operation in enhanced_catalog.operations
        ],
        "notes": enhanced_catalog.notes,
    }
    prompt_index_payload = {
        "catalog_prompts": [
            {
                "name": prompt.name,
                "title": prompt.title,
                "description": prompt.description,
                "arguments": prompt.arguments,
            }
            for prompt in build_default_catalog_prompt_definitions(enhanced_catalog)
        ],
        "operation_prompts": [
            {
                "operation_slug": operation.operation_slug,
                "prompts": [
                    {
                        "name": prompt.name,
                        "title": prompt.title,
                        "description": prompt.description,
                        "arguments": prompt.arguments,
                    }
                    for prompt in operation.prompt_templates
                ],
            }
            for operation in enhanced_catalog.operations
            if operation.prompt_templates
        ],
    }

    return [
        CatalogResourceDefinition(
            kind="resource",
            uri=f"oas2mcp://{enhanced_catalog.catalog_slug}/catalog/summary",
            name="catalog_summary",
            title="Catalog summary",
            description="Inspect the exported catalog-level summary and operation index.",
            payload=catalog_summary_payload,
            version=version,
            tags=["catalog", "summary"],
            meta=base_meta,
        ),
        CatalogResourceDefinition(
            kind="resource",
            uri=f"oas2mcp://{enhanced_catalog.catalog_slug}/catalog/prompts",
            name="prompt_index",
            title="Prompt index",
            description="Inspect catalog-level and operation-level prompt definitions.",
            payload=prompt_index_payload,
            version=version,
            tags=["catalog", "prompt"],
            meta=base_meta,
        ),
        CatalogResourceDefinition(
            kind="resource_template",
            uri=f"oas2mcp://{enhanced_catalog.catalog_slug}/operations/{{operation_slug}}",
            name="operation_metadata",
            title="Operation metadata",
            description="Inspect exported metadata for one operation slug.",
            handler="operation_metadata",
            arguments=["operation_slug"],
            version=version,
            tags=["catalog", "operation"],
            meta=base_meta,
        ),
        CatalogResourceDefinition(
            kind="resource_template",
            uri=f"oas2mcp://{enhanced_catalog.catalog_slug}/namespaces/{{namespace}}/operations",
            name="namespace_operations",
            title="Namespace operations",
            description="Inspect exported operations grouped under one namespace.",
            handler="namespace_operations",
            arguments=["namespace"],
            version=version,
            tags=["catalog", "namespace"],
            meta=base_meta,
        ),
    ]


def _list_namespaces(enhanced_catalog: EnhancedCatalog) -> list[str]:
    """Return a stable list of non-empty namespaces."""
    return sorted(
        {
            operation.namespace
            for operation in enhanced_catalog.operations
            if operation.namespace
        }
    )
