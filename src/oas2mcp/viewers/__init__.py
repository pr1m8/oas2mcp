"""Rich viewers for ``oas2mcp``.

Purpose:
    Render normalized API catalogs and MCP classification results with readable
    Rich console output.

Design:
    - Keep raw OpenAPI catalog viewers separate from MCP classification viewers.
    - Expose a small, stable set of rendering helpers.

Attributes:
    __all__: Curated public exports for Rich viewer helpers.

Examples:
    .. code-block:: python

        from rich.console import Console

        from oas2mcp.viewers import render_catalog_summary

        render_catalog_summary(catalog, console=Console())
"""

from oas2mcp.viewers.classification import (
    render_mcp_bundle_summary,
    render_mcp_candidate_detail,
    render_operation_agent_context_preview,
)
from oas2mcp.viewers.summary import (
    render_catalog_summary,
    render_operation_detail,
)

__all__ = [
    "render_catalog_summary",
    "render_operation_detail",
    "render_mcp_bundle_summary",
    "render_mcp_candidate_detail",
    "render_operation_agent_context_preview",
]
