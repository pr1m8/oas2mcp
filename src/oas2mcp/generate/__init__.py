"""Export and FastMCP bootstrap helpers for ``oas2mcp``.

Purpose:
    Provide a small public surface for artifact export, generated metadata, and
    FastMCP bootstrap helpers used by the summarize-and-enhance pipeline.

Design:
    - Keep exported artifact helpers grouped under a real Python package.
    - Re-export the small set of helpers that are useful to callers without
      forcing them to import submodules directly.
"""

from oas2mcp.generate.config import ExportConfig
from oas2mcp.generate.export import (
    build_fastmcp_config,
    build_operation_notes_map,
    export_enhanced_catalog_bundle,
)
from oas2mcp.generate.fastmcp_app import (
    build_fastmcp_from_exported_artifacts,
    build_fastmcp_from_loaded_artifacts,
    register_exported_prompts,
)
from oas2mcp.generate.models import EnhancedCatalog

__all__ = [
    "EnhancedCatalog",
    "ExportConfig",
    "build_fastmcp_config",
    "build_fastmcp_from_exported_artifacts",
    "build_fastmcp_from_loaded_artifacts",
    "build_operation_notes_map",
    "export_enhanced_catalog_bundle",
    "register_exported_prompts",
]
