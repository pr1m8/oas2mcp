"""Rich viewers for ``oas2mcp``.

Purpose:
    Render normalized API catalogs with readable Rich console output.

Design:
    - Keep rendering logic independent from loading and normalization.
    - Offer both high-level summary views and focused per-operation detail
      views.

Attributes:
    __all__: Curated public exports for Rich viewer helpers.

Examples:
    .. code-block:: python

        from rich.console import Console

        from oas2mcp.viewers import render_catalog_summary

        render_catalog_summary(catalog, console=Console())
"""

from oas2mcp.viewers.summary import (
    render_catalog_summary,
    render_operation_detail,
)

__all__ = [
    "render_catalog_summary",
    "render_operation_detail",
]
