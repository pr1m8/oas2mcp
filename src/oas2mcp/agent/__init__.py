"""Agent layer for ``oas2mcp``.

Purpose:
    Provide agent-oriented submodules for summarization and later enhancement
    workflows built on top of normalized OpenAPI catalogs and deterministic MCP
    preparation outputs.

Design:
    - Keep the agent layer separate from loading, normalization, viewing, and
      deterministic classification.
    - Centralize shared runtime context and base agent construction.
    - Allow each concrete workflow to live in its own submodule.

Attributes:
    __all__: Curated public exports for the agent layer.

Examples:
    .. code-block:: python

        from oas2mcp.agent.runtime import Oas2McpRuntimeContext
"""

__all__ = []
