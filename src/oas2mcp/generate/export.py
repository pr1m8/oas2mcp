"""Export helpers for enhanced catalog artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from oas2mcp.generate.config import ExportConfig
from oas2mcp.generate.models import EnhancedCatalog


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
            "tool_name": operation.tool_name,
            "resource_uri": operation.resource_uri,
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
        "source_url": enhanced_catalog.source_url,
        "mcp_names": build_fastmcp_name_map(enhanced_catalog),
        "operations": build_operation_notes_map(enhanced_catalog),
    }


def _derive_fastmcp_component_name(operation: Any) -> str:
    """Choose a FastMCP-safe component name from exported operation metadata."""
    if operation.tool_name:
        return operation.tool_name

    if operation.resource_uri:
        parsed = urlparse(operation.resource_uri)
        segments = [segment for segment in parsed.path.split("/") if segment]
        for segment in reversed(segments):
            if not segment.startswith("{"):
                return segment

    return operation.operation_slug
