"""Export helpers for enhanced catalog artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from oas2mcp.generate.models import EnhancedCatalog


def export_enhanced_catalog_json(
    *,
    enhanced_catalog: EnhancedCatalog,
    output_path: str | Path,
) -> Path:
    """Write the enhanced catalog to disk as JSON."""
    resolved_path = Path(output_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_path.write_text(
        enhanced_catalog.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return resolved_path


def build_fastmcp_name_map(
    enhanced_catalog: EnhancedCatalog,
) -> dict[str, str]:
    """Build operationId -> MCP name overrides for FastMCP bootstrapping."""
    mapping: dict[str, str] = {}

    for operation in enhanced_catalog.operations:
        chosen_name = operation.tool_name or operation.resource_uri
        if not chosen_name:
            continue
        mapping[operation.operation_slug] = chosen_name

    return mapping


def build_operation_notes_map(
    enhanced_catalog: EnhancedCatalog,
) -> dict[str, dict[str, Any]]:
    """Build lightweight per-operation metadata for later export steps."""
    result: dict[str, dict[str, Any]] = {}

    for operation in enhanced_catalog.operations:
        result[operation.operation_slug] = {
            "final_kind": operation.final_kind,
            "namespace": operation.namespace,
            "title": operation.title,
            "description": operation.description,
            "requires_confirmation": operation.requires_confirmation,
            "auth_notes": operation.auth_notes,
            "notes": operation.notes,
            "prompt_templates": [
                prompt.model_dump() for prompt in operation.prompt_templates
            ],
        }

    return result
