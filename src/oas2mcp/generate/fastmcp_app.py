"""FastMCP bootstrap helpers from exported ``oas2mcp`` artifacts."""

from __future__ import annotations

import inspect
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping

import httpx
from fastmcp import FastMCP
from fastmcp.server.providers.openapi import MCPType, RouteMap


def load_json_file(path: str | Path) -> dict[str, Any]:
    """Load a JSON file from disk."""
    resolved_path = Path(path)
    return json.loads(resolved_path.read_text(encoding="utf-8"))


def fetch_openapi_spec(source_url: str, *, timeout: float = 30.0) -> dict[str, Any]:
    """Fetch an OpenAPI specification from a URL."""
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        response = client.get(source_url)
        response.raise_for_status()
        data = response.json()

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object from {source_url!r}.")
    return data


def infer_base_url_from_spec(openapi_spec: dict[str, Any]) -> str:
    """Infer the base URL from the first OpenAPI server entry."""
    servers = openapi_spec.get("servers", [])
    if not servers:
        raise ValueError("OpenAPI spec does not define any servers.")
    first_server = servers[0]
    url = first_server.get("url")
    if not isinstance(url, str) or not url.strip():
        raise ValueError("OpenAPI spec server entry does not include a valid URL.")
    return url


def build_default_headers_from_env() -> dict[str, str]:
    """Build optional upstream headers from environment variables."""
    headers: dict[str, str] = {}

    bearer_token = os.getenv("UPSTREAM_BEARER_TOKEN")
    api_key = os.getenv("UPSTREAM_API_KEY")
    api_key_header = os.getenv("UPSTREAM_API_KEY_HEADER", "api_key")

    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    if api_key:
        headers[api_key_header] = api_key

    return headers


def build_semantic_route_maps() -> list[RouteMap]:
    """Restore semantic OpenAPI mapping for FastMCP.

    GET with path params -> RESOURCE_TEMPLATE
    other GET -> RESOURCE
    everything else falls through to default TOOL mapping.
    """
    return [
        RouteMap(
            methods=["GET"],
            pattern=r".*\{.*\}.*",
            mcp_type=MCPType.RESOURCE_TEMPLATE,
        ),
        RouteMap(
            methods=["GET"],
            pattern=r".*",
            mcp_type=MCPType.RESOURCE,
        ),
    ]


def build_export_aware_route_map_fn(
    fastmcp_config: Mapping[str, Any],
) -> Callable[[Any, MCPType], MCPType | None]:
    """Build a route-mapping override that respects exported operation kinds."""
    operation_kinds = {
        metadata["operation_id"]: metadata["final_kind"]
        for metadata in fastmcp_config.get("operations", {}).values()
        if metadata.get("operation_id") and metadata.get("final_kind")
    }

    def route_map_fn(route: Any, default_type: MCPType) -> MCPType | None:
        operation_id = getattr(route, "operation_id", None)
        final_kind = operation_kinds.get(operation_id)
        if final_kind == "tool":
            return MCPType.TOOL
        if final_kind == "resource":
            has_path_params = any(
                getattr(parameter, "location", None) == "path"
                for parameter in getattr(route, "parameters", [])
            )
            if has_path_params:
                return MCPType.RESOURCE_TEMPLATE
            return MCPType.RESOURCE
        return default_type

    return route_map_fn


def build_fastmcp_name_overrides(
    fastmcp_config: Mapping[str, Any],
) -> dict[str, str]:
    """Return operationId -> FastMCP component name overrides."""
    configured_names = fastmcp_config.get("mcp_names", {})
    if configured_names:
        return {
            str(operation_id): str(name)
            for operation_id, name in configured_names.items()
        }

    generated_names: dict[str, str] = {}
    for operation_slug, metadata in fastmcp_config.get("operations", {}).items():
        operation_id = metadata.get("operation_id")
        if not operation_id:
            continue

        tool_name = metadata.get("tool_name")
        resource_uri = metadata.get("resource_uri")
        if tool_name:
            generated_names[operation_id] = str(tool_name)
            continue
        if isinstance(resource_uri, str):
            generated_names[operation_id] = resource_uri.rstrip("/").split("/")[-1]
            continue

        generated_names[operation_id] = str(operation_slug)

    return generated_names


def build_fastmcp_from_loaded_artifacts(
    *,
    openapi_spec: Mapping[str, Any],
    fastmcp_config: Mapping[str, Any],
    server_name: str | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    client: httpx.AsyncClient | None = None,
) -> FastMCP:
    """Build a FastMCP server from already loaded OpenAPI and config data."""
    resolved_headers = {**build_default_headers_from_env(), **(headers or {})}
    resolved_client = client or httpx.AsyncClient(
        base_url=infer_base_url_from_spec(dict(openapi_spec)),
        headers=resolved_headers,
        timeout=timeout,
    )

    return FastMCP.from_openapi(
        openapi_spec=dict(openapi_spec),
        client=resolved_client,
        name=server_name or fastmcp_config.get("catalog_name", "OpenAPI Server"),
        mcp_names=build_fastmcp_name_overrides(fastmcp_config),
        route_maps=build_semantic_route_maps(),
        route_map_fn=build_export_aware_route_map_fn(fastmcp_config),
    )


def build_fastmcp_from_exported_artifacts(
    *,
    source_url: str,
    fastmcp_config_path: str | Path,
    server_name: str | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    client: httpx.AsyncClient | None = None,
) -> FastMCP:
    """Build a FastMCP server from exported oas2mcp artifacts."""
    openapi_spec = fetch_openapi_spec(source_url, timeout=timeout)
    fastmcp_config = load_json_file(fastmcp_config_path)

    return build_fastmcp_from_loaded_artifacts(
        openapi_spec=openapi_spec,
        fastmcp_config=fastmcp_config,
        server_name=server_name,
        headers=headers,
        timeout=timeout,
        client=client,
    )


def register_exported_prompts(
    mcp: FastMCP,
    fastmcp_config_path: str | Path | Mapping[str, Any],
) -> None:
    """Register exported prompt templates on a FastMCP server."""
    if isinstance(fastmcp_config_path, Mapping):
        fastmcp_config = dict(fastmcp_config_path)
    else:
        fastmcp_config = load_json_file(fastmcp_config_path)
    operations = fastmcp_config.get("operations", {})

    for operation_slug, metadata in operations.items():
        for prompt_data in metadata.get("prompt_templates", []):
            prompt_name = prompt_data["name"]
            prompt_title = prompt_data.get("title", prompt_name)
            prompt_description = prompt_data.get("description", "")
            prompt_arguments = list(prompt_data.get("arguments", []))

            def _make_prompt(
                *,
                name: str,
                title: str,
                description: str,
                arguments: list[str],
                operation_slug_value: str,
            ) -> Callable[..., str]:
                def _prompt(**kwargs: str) -> str:
                    argument_lines = []
                    for argument in arguments:
                        value = kwargs.get(argument, f"<{argument}>")
                        argument_lines.append(f"- {argument}: {value}")

                    joined = (
                        "\n".join(argument_lines)
                        if argument_lines
                        else "- no explicit arguments"
                    )
                    return (
                        f"{description}\n\n"
                        f"Operation slug: {operation_slug_value}\n"
                        f"Arguments:\n{joined}"
                    )

                _prompt.__name__ = name.replace("-", "_")
                _prompt.__doc__ = description or title
                _prompt.__annotations__ = {
                    **{argument: str for argument in arguments},
                    "return": str,
                }
                _prompt.__signature__ = inspect.Signature(
                    parameters=[
                        inspect.Parameter(
                            argument,
                            kind=inspect.Parameter.KEYWORD_ONLY,
                            annotation=str,
                            default="",
                        )
                        for argument in arguments
                    ],
                    return_annotation=str,
                )
                return _prompt

            prompt_fn = _make_prompt(
                name=prompt_name,
                title=prompt_title,
                description=prompt_description,
                arguments=prompt_arguments,
                operation_slug_value=operation_slug,
            )
            mcp.prompt(
                name=prompt_name,
                title=prompt_title,
                description=prompt_description,
            )(prompt_fn)
