"""FastMCP bootstrap helpers from enhanced OpenAPI context."""

from __future__ import annotations

import httpx
from fastmcp import FastMCP

from oas2mcp.generate.export import build_fastmcp_name_map
from oas2mcp.generate.models import EnhancedCatalog


def build_fastmcp_from_openapi(
    *,
    openapi_spec: dict,
    base_url: str,
    enhanced_catalog: EnhancedCatalog,
    server_name: str | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> FastMCP:
    """Build a FastMCP server from an OpenAPI spec and enhancement metadata."""
    client = httpx.AsyncClient(
        base_url=base_url,
        headers=headers or {},
        timeout=timeout,
    )

    return FastMCP.from_openapi(
        openapi_spec=openapi_spec,
        client=client,
        name=server_name or enhanced_catalog.catalog_name,
        mcp_names=build_fastmcp_name_map(enhanced_catalog),
    )
