"""FastMCP bootstrap helpers from exported oas2mcp artifacts.

Purpose:
    Build a FastMCP server from the original OpenAPI spec plus exported
    enhancement metadata.

Design:
    - Reuse the original OpenAPI spec as the transport/source of truth.
    - Apply exported name overrides and lightweight metadata from the enhanced
      catalog artifacts.
    - Keep bootstrap logic separate from future richer enhanced-OpenAPI export.

Examples:
    .. code-block:: python

        from pathlib import Path

        mcp = build_fastmcp_from_exported_artifacts(
            source_url="https://petstore3.swagger.io/api/v3/openapi.json",
            fastmcp_config_path=Path("data/exports/petstore_fastmcp_config.json"),
        )
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
from fastmcp import FastMCP


def load_json_file(path: str | Path) -> dict[str, Any]:
    """Load a JSON file from disk.

    Args:
        path: The JSON file path.

    Returns:
        The parsed JSON object.

    Raises:
        FileNotFoundError: If the path does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    resolved_path = Path(path)
    return json.loads(resolved_path.read_text(encoding="utf-8"))


def fetch_openapi_spec(source_url: str, *, timeout: float = 30.0) -> dict[str, Any]:
    """Fetch an OpenAPI specification from a URL.

    Args:
        source_url: The OpenAPI JSON URL.
        timeout: Request timeout in seconds.

    Returns:
        The parsed OpenAPI spec as a dictionary.

    Raises:
        httpx.HTTPError: If the request fails.
        ValueError: If the body is empty or not a JSON object.
    """
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        response = client.get(source_url)
        response.raise_for_status()
        data = response.json()

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object from {source_url!r}.")
    return data


def infer_base_url_from_spec(openapi_spec: dict[str, Any]) -> str:
    """Infer the base URL from the first OpenAPI server entry.

    Args:
        openapi_spec: The OpenAPI specification.

    Returns:
        The first configured server URL.

    Raises:
        ValueError: If no usable server URL is present.
    """
    servers = openapi_spec.get("servers", [])
    if not servers:
        raise ValueError("OpenAPI spec does not define any servers.")
    first_server = servers[0]
    url = first_server.get("url")
    if not isinstance(url, str) or not url.strip():
        raise ValueError("OpenAPI spec server entry does not include a valid URL.")
    return url


def build_fastmcp_from_exported_artifacts(
    *,
    source_url: str,
    fastmcp_config_path: str | Path,
    server_name: str | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> FastMCP:
    """Build a FastMCP server from exported oas2mcp artifacts.

    Args:
        source_url: The original OpenAPI JSON URL.
        fastmcp_config_path: Path to the exported FastMCP config JSON.
        server_name: Optional explicit FastMCP server name.
        headers: Optional HTTP headers for upstream API access.
        timeout: HTTP client timeout in seconds.

    Returns:
        A bootstrapped ``FastMCP`` server.

    Raises:
        httpx.HTTPError: If the OpenAPI fetch fails.
        ValueError: If required config fields are missing.
    """
    openapi_spec = fetch_openapi_spec(source_url, timeout=timeout)
    fastmcp_config = load_json_file(fastmcp_config_path)

    base_url = infer_base_url_from_spec(openapi_spec)
    mcp_names = fastmcp_config.get("mcp_names", {})
    catalog_name = fastmcp_config.get("catalog_name", "OpenAPI Server")

    client = httpx.AsyncClient(
        base_url=base_url,
        headers=headers or {},
        timeout=timeout,
    )

    return FastMCP.from_openapi(
        openapi_spec=openapi_spec,
        client=client,
        name=server_name or catalog_name,
        mcp_names=mcp_names,
    )
