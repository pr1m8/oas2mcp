"""Classification helpers for ``oas2mcp``.

Purpose:
    Convert normalized operations into deterministic MCP-oriented candidates.

Design:
    - Keep first-pass classification rule-based.
    - Let agents improve or override these results later.

Attributes:
    __all__: Curated public exports for the classification layer.

Examples:
    .. code-block:: python

        from oas2mcp.classify import classify_catalog
"""

from oas2mcp.classify.operations import (
    classify_catalog,
    classify_operation,
)

__all__ = [
    "classify_catalog",
    "classify_operation",
]
