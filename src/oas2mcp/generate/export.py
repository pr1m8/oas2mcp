"""Export helpers for enhanced catalog artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from oas2mcp.generate.config import ExportConfig
from oas2mcp.generate.models import (
    CatalogPromptDefinition,
    CatalogResourceDefinition,
    EnhancedCatalog,
)
from oas2mcp.generate.surface_defaults import (
    build_default_catalog_prompt_definitions,
    build_default_catalog_resource_definitions,
    build_default_server_instructions,
)


def export_enhanced_catalog_bundle(
    *,
    enhanced_catalog: EnhancedCatalog,
    config: ExportConfig,
) -> dict[str, Path]:
    """Write enhanced catalog artifacts to disk.

    Args:
        enhanced_catalog: The enhanced catalog to export.
        config: Export configuration.

    Returns:
        dict[str, Path]: A mapping of artifact names to written paths.

    Raises:
        None.

    Examples:
        .. code-block:: python

            outputs = export_enhanced_catalog_bundle(
                enhanced_catalog=enhanced_catalog,
                config=config,
            )
    """
    slug = enhanced_catalog.catalog_slug
    export_dir = config.resolved_export_dir
    export_dir.mkdir(parents=True, exist_ok=True)

    written_paths: dict[str, Path] = {}

    enhanced_catalog_path = export_dir / f"{slug}_enhanced_catalog.json"
    enhanced_catalog_path.write_text(
        enhanced_catalog.model_dump_json(indent=2),
        encoding="utf-8",
    )
    written_paths["enhanced_catalog"] = enhanced_catalog_path

    if config.write_operation_notes:
        operation_notes_path = export_dir / f"{slug}_operation_notes.json"
        operation_notes_path.write_text(
            json.dumps(
                build_operation_notes_map(enhanced_catalog),
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        written_paths["operation_notes"] = operation_notes_path

    if config.write_surface_plan and enhanced_catalog.surface_plan is not None:
        surface_plan_path = export_dir / f"{slug}_surface_plan.json"
        surface_plan_path.write_text(
            enhanced_catalog.surface_plan.model_dump_json(indent=2),
            encoding="utf-8",
        )
        written_paths["surface_plan"] = surface_plan_path

    if config.write_fastmcp_config:
        fastmcp_config_path = export_dir / f"{slug}_fastmcp_config.json"
        fastmcp_config_path.write_text(
            json.dumps(
                build_fastmcp_config(enhanced_catalog),
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        written_paths["fastmcp_config"] = fastmcp_config_path

    if config.write_root_snapshot:
        snapshot_name = config.root_snapshot_name or f"{slug}.enhanced.json"
        root_snapshot_path = config.project_root / snapshot_name
        root_snapshot_path.write_text(
            enhanced_catalog.model_dump_json(indent=2),
            encoding="utf-8",
        )
        written_paths["root_snapshot"] = root_snapshot_path

    return written_paths


def build_fastmcp_name_map(
    enhanced_catalog: EnhancedCatalog,
) -> dict[str, str]:
    """Build operationId -> FastMCP component-name overrides.

    Args:
        enhanced_catalog: The enhanced catalog.

    Returns:
        dict[str, str]: OpenAPI operationId to chosen FastMCP component name.

    Raises:
        None.
    """
    mapping: dict[str, str] = {}

    for operation in enhanced_catalog.operations:
        if not operation.operation_id:
            continue
        mapping[operation.operation_id] = _derive_fastmcp_component_name(operation)

    return mapping


def build_operation_notes_map(
    enhanced_catalog: EnhancedCatalog,
) -> dict[str, dict[str, Any]]:
    """Build lightweight per-operation export metadata.

    Args:
        enhanced_catalog: The enhanced catalog.

    Returns:
        dict[str, dict[str, Any]]: Per-operation export metadata.

    Raises:
        None.
    """
    result: dict[str, dict[str, Any]] = {}

    for operation in enhanced_catalog.operations:
        result[operation.operation_slug] = {
            "operation_id": operation.operation_id,
            "final_kind": operation.final_kind,
            "namespace": operation.namespace,
            "title": operation.title,
            "description": operation.description,
            "component_name": operation.component_name,
            "tool_name": operation.tool_name,
            "resource_uri": operation.resource_uri,
            "component_version": operation.component_version,
            "component_tags": operation.component_tags,
            "component_meta": operation.component_meta,
            "component_annotations": operation.component_annotations,
            "requires_confirmation": operation.requires_confirmation,
            "auth_notes": operation.auth_notes,
            "notes": operation.notes,
            "prompt_templates": [
                prompt.model_dump() for prompt in operation.prompt_templates
            ],
        }

    return result


def build_fastmcp_config(
    enhanced_catalog: EnhancedCatalog,
) -> dict[str, Any]:
    """Build lightweight FastMCP bootstrap metadata.

    Args:
        enhanced_catalog: The enhanced catalog.

    Returns:
        dict[str, Any]: FastMCP bootstrap metadata.

    Raises:
        None.
    """
    return {
        "catalog_name": enhanced_catalog.catalog_name,
        "catalog_slug": enhanced_catalog.catalog_slug,
        "catalog_version": enhanced_catalog.catalog_version,
        "source_uri": enhanced_catalog.source_url,
        "source_url": enhanced_catalog.source_url,
        "server_instructions": build_server_instructions(enhanced_catalog),
        "surface_notes": (
            enhanced_catalog.surface_plan.notes
            if enhanced_catalog.surface_plan is not None
            else []
        ),
        "catalog_prompts": [
            prompt.model_dump()
            for prompt in build_catalog_prompt_definitions(enhanced_catalog)
        ],
        "catalog_resources": [
            resource.model_dump()
            for resource in build_catalog_resource_definitions(enhanced_catalog)
        ],
        "mcp_names": build_fastmcp_name_map(enhanced_catalog),
        "operations": build_operation_notes_map(enhanced_catalog),
    }


def _derive_fastmcp_component_name(operation: Any) -> str:
    """Choose a FastMCP-safe component name from exported operation metadata."""
    if operation.tool_name:
        return operation.tool_name

    if operation.component_name:
        return operation.component_name

    if operation.resource_uri:
        derived_name = _derive_component_name_from_uri(operation.resource_uri)
        if derived_name:
            return derived_name

    return operation.operation_slug


def _derive_component_name_from_uri(resource_uri: str) -> str | None:
    """Return a stable FastMCP component name from a resource URI or template."""
    uri_without_query_template = resource_uri.split("{?", 1)[0]
    _, _, path_part = uri_without_query_template.partition("://")
    if "/" in path_part:
        _, _, path_part = path_part.partition("/")
    segments = [segment for segment in path_part.split("/") if segment]
    for segment in reversed(segments):
        if not segment.startswith("{"):
            return segment
    return None


def build_server_instructions(enhanced_catalog: EnhancedCatalog) -> str:
    """Build concise FastMCP server instructions from the catalog summary."""
    if enhanced_catalog.surface_plan is not None:
        planned_instructions = enhanced_catalog.surface_plan.server_instructions.strip()
        if planned_instructions:
            return planned_instructions
    return build_default_server_instructions(enhanced_catalog)


def build_catalog_prompt_definitions(
    enhanced_catalog: EnhancedCatalog,
) -> list[CatalogPromptDefinition]:
    """Build catalog-level prompt definitions for FastMCP registration."""
    if enhanced_catalog.surface_plan is not None:
        return [
            CatalogPromptDefinition.model_validate(prompt.model_dump())
            for prompt in enhanced_catalog.surface_plan.catalog_prompts
        ]
    return build_default_catalog_prompt_definitions(enhanced_catalog)


def build_catalog_resource_definitions(
    enhanced_catalog: EnhancedCatalog,
) -> list[CatalogResourceDefinition]:
    """Build catalog-level resources and resource templates."""
    if enhanced_catalog.surface_plan is not None:
        return [
            CatalogResourceDefinition.model_validate(resource.model_dump())
            for resource in enhanced_catalog.surface_plan.catalog_resources
        ]
    return build_default_catalog_resource_definitions(enhanced_catalog)
