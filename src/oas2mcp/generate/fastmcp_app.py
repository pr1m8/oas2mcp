"""FastMCP bootstrap helpers from exported ``oas2mcp`` artifacts."""

from __future__ import annotations

import inspect
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping

import httpx
from fastmcp import FastMCP
from fastmcp.exceptions import ResourceError
from fastmcp.server.providers.openapi import MCPType, RouteMap

from oas2mcp.generate.models import (
    CatalogPromptDefinition,
    CatalogResourceDefinition,
)
from oas2mcp.loaders.openapi import load_openapi_spec_dict


def load_json_file(path: str | Path) -> dict[str, Any]:
    """Load a JSON file from disk."""
    resolved_path = Path(path)
    return json.loads(resolved_path.read_text(encoding="utf-8"))


def fetch_openapi_spec(
    source: str | Path,
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Load an OpenAPI specification from any supported source."""
    return load_openapi_spec_dict(source, timeout=timeout)


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
            return MCPType.RESOURCE
        if final_kind == "resource_template":
            return MCPType.RESOURCE_TEMPLATE
        if final_kind in {"exclude", "prompt"}:
            return MCPType.EXCLUDE
        return default_type

    return route_map_fn


def build_export_aware_component_fn(
    fastmcp_config: Mapping[str, Any],
) -> Callable[[Any, Any], Any]:
    """Build a component mutator that applies exported metadata to FastMCP."""
    operation_metadata = {
        metadata["operation_id"]: metadata
        for metadata in fastmcp_config.get("operations", {}).values()
        if metadata.get("operation_id")
    }

    def component_fn(route: Any, component: Any) -> Any:
        operation_id = getattr(route, "operation_id", None)
        metadata = operation_metadata.get(operation_id)
        if metadata is None:
            return component

        title = metadata.get("title")
        description = metadata.get("description")
        resource_uri = metadata.get("resource_uri")
        component_version = metadata.get("component_version")
        component_tags = metadata.get("component_tags") or []
        component_meta = metadata.get("component_meta") or {}
        component_annotations = metadata.get("component_annotations") or {}
        final_kind = metadata.get("final_kind")

        if title and hasattr(component, "title"):
            component.title = title
        if description and hasattr(component, "description"):
            component.description = description
        if component_version and hasattr(component, "version"):
            component.version = component_version
        if component_tags and hasattr(component, "tags"):
            component.tags = set(component_tags)
        if component_meta and hasattr(component, "meta"):
            existing_meta = getattr(component, "meta", None) or {}
            component.meta = {**existing_meta, **component_meta}
        if component_annotations and hasattr(component, "annotations"):
            component.annotations = component_annotations

        if isinstance(resource_uri, str):
            if final_kind == "resource" and hasattr(component, "uri"):
                component.uri = resource_uri
            if final_kind == "resource_template" and hasattr(component, "uri_template"):
                component.uri_template = resource_uri
                if hasattr(component, "parameters"):
                    component.parameters = _build_resource_template_parameters(route)

        return component

    return component_fn


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
        component_name = metadata.get("component_name")
        resource_uri = metadata.get("resource_uri")
        if tool_name:
            generated_names[operation_id] = str(tool_name)
            continue
        if component_name:
            generated_names[operation_id] = str(component_name)
            continue
        if isinstance(resource_uri, str):
            derived_name = _derive_component_name_from_uri(resource_uri)
            if derived_name:
                generated_names[operation_id] = derived_name
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
        mcp_component_fn=build_export_aware_component_fn(fastmcp_config),
        instructions=fastmcp_config.get("server_instructions"),
        version=fastmcp_config.get("catalog_version"),
    )


def build_fastmcp_from_exported_artifacts(
    *,
    source: str | Path | None = None,
    source_url: str | Path | None = None,
    fastmcp_config_path: str | Path,
    server_name: str | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    client: httpx.AsyncClient | None = None,
) -> FastMCP:
    """Build a FastMCP server from exported oas2mcp artifacts."""
    fastmcp_config = load_json_file(fastmcp_config_path)
    resolved_source = (
        source
        or source_url
        or fastmcp_config.get("source_uri")
        or fastmcp_config.get("source_url")
    )
    if resolved_source is None:
        raise ValueError(
            "An OpenAPI source must be provided directly or be present in the exported config."
        )
    openapi_spec = fetch_openapi_spec(resolved_source, timeout=timeout)

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
    fastmcp_config = _load_fastmcp_config_mapping(fastmcp_config_path)

    for prompt_definition in _iter_prompt_definitions(fastmcp_config):
        prompt_fn = _make_prompt_function(prompt_definition)
        mcp.prompt(
            name=prompt_definition.name,
            title=prompt_definition.title,
            description=prompt_definition.description,
            version=prompt_definition.version,
            tags=set(prompt_definition.tags) if prompt_definition.tags else None,
            meta=prompt_definition.meta or None,
        )(prompt_fn)


def register_exported_resources(
    mcp: FastMCP,
    fastmcp_config_path: str | Path | Mapping[str, Any],
) -> None:
    """Register exported catalog resources on a FastMCP server."""
    fastmcp_config = _load_fastmcp_config_mapping(fastmcp_config_path)

    for resource_definition in _iter_resource_definitions(fastmcp_config):
        tags = set(resource_definition.tags) if resource_definition.tags else None
        annotations = resource_definition.annotations or None
        meta = resource_definition.meta or None

        if resource_definition.handler == "static":
            resource_fn = _make_static_resource_function(
                resource_definition.payload,
                resource_definition.description,
            )
        elif resource_definition.handler == "operation_metadata":
            resource_fn = _make_operation_metadata_resource_function(
                fastmcp_config=fastmcp_config,
            )
        elif resource_definition.handler == "namespace_operations":
            resource_fn = _make_namespace_operations_resource_function(
                fastmcp_config=fastmcp_config,
            )
        else:
            raise ValueError(
                f"Unsupported exported resource handler: {resource_definition.handler!r}"
            )

        mcp.resource(
            resource_definition.uri,
            name=resource_definition.name,
            title=resource_definition.title,
            description=resource_definition.description,
            version=resource_definition.version,
            mime_type=resource_definition.mime_type,
            tags=tags,
            annotations=annotations,
            meta=meta,
        )(resource_fn)


def _load_fastmcp_config_mapping(
    fastmcp_config_path: str | Path | Mapping[str, Any],
) -> dict[str, Any]:
    """Load FastMCP config from either a mapping or a JSON file."""
    if isinstance(fastmcp_config_path, Mapping):
        return dict(fastmcp_config_path)
    return load_json_file(fastmcp_config_path)


def _iter_prompt_definitions(
    fastmcp_config: Mapping[str, Any],
) -> list[CatalogPromptDefinition]:
    """Return catalog-level and per-operation prompt definitions."""
    prompt_definitions = [
        CatalogPromptDefinition.model_validate(prompt_data)
        for prompt_data in fastmcp_config.get("catalog_prompts", [])
    ]

    for operation_slug, metadata in fastmcp_config.get("operations", {}).items():
        for prompt_data in metadata.get("prompt_templates", []):
            prompt_template = dict(prompt_data)
            prompt_template.setdefault(
                "template",
                (
                    f"{prompt_data.get('description', '')}\n\n"
                    f"Operation slug: {operation_slug}\n"
                    "Arguments:\n"
                    + "\n".join(
                        f"- {argument}: {{{argument}}}"
                        for argument in prompt_data.get("arguments", [])
                    )
                ).strip(),
            )
            prompt_template.setdefault(
                "meta",
                {
                    "generated_by": "oas2mcp",
                    "operation_slug": operation_slug,
                },
            )
            prompt_definitions.append(
                CatalogPromptDefinition.model_validate(prompt_template)
            )

    return prompt_definitions


def _iter_resource_definitions(
    fastmcp_config: Mapping[str, Any],
) -> list[CatalogResourceDefinition]:
    """Return exported catalog-level resource definitions."""
    return [
        CatalogResourceDefinition.model_validate(resource_data)
        for resource_data in fastmcp_config.get("catalog_resources", [])
    ]


def _make_prompt_function(
    prompt_definition: CatalogPromptDefinition,
) -> Callable[..., str]:
    """Build a callable prompt function from exported prompt metadata."""
    arguments = list(prompt_definition.arguments)
    template = prompt_definition.template

    def _prompt(**kwargs: str) -> str:
        return template.format_map(_PromptFormatDict(kwargs))

    _prompt.__name__ = prompt_definition.name.replace("-", "_")
    _prompt.__doc__ = prompt_definition.description or prompt_definition.title
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


def _make_static_resource_function(
    payload: Any,
    description: str,
) -> Callable[[], Any]:
    """Build a simple static resource function."""

    def _resource() -> Any:
        return payload

    _resource.__doc__ = description
    return _resource


def _make_operation_metadata_resource_function(
    *,
    fastmcp_config: Mapping[str, Any],
) -> Callable[[str], Any]:
    """Build a resource-template function for exported operation metadata."""

    def _resource(operation_slug: str) -> Any:
        operation = fastmcp_config.get("operations", {}).get(operation_slug)
        if operation is None:
            raise ResourceError(
                f"Unknown operation slug {operation_slug!r} in exported FastMCP metadata."
            )
        return operation

    _resource.__doc__ = "Return exported metadata for one operation slug."
    return _resource


def _make_namespace_operations_resource_function(
    *,
    fastmcp_config: Mapping[str, Any],
) -> Callable[[str], Any]:
    """Build a resource-template function for exported namespace operations."""

    def _resource(namespace: str) -> Any:
        matching_operations = [
            operation
            for operation in fastmcp_config.get("operations", {}).values()
            if operation.get("namespace") == namespace
        ]
        if not matching_operations:
            raise ResourceError(
                f"Unknown namespace {namespace!r} in exported FastMCP metadata."
            )
        return {
            "namespace": namespace,
            "operations": matching_operations,
        }

    _resource.__doc__ = "Return exported metadata for one namespace."
    return _resource


def _build_resource_template_parameters(route: Any) -> dict[str, Any]:
    """Build a JSON schema for resource-template parameters."""
    properties: dict[str, Any] = {}
    required: list[str] = []

    for parameter in getattr(route, "parameters", []):
        name = getattr(parameter, "name", None)
        if not isinstance(name, str) or not name:
            continue

        schema = getattr(parameter, "schema", None)
        schema_dict = dict(schema) if isinstance(schema, Mapping) else {}
        if not schema_dict:
            schema_dict = {"type": "string"}
        properties[name] = schema_dict

        if bool(getattr(parameter, "required", False)):
            required.append(name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def _derive_component_name_from_uri(resource_uri: str) -> str | None:
    """Derive a stable component name from a resource URI or URI template."""
    uri_without_query_template = resource_uri.split("{?", 1)[0]
    _, _, path_part = uri_without_query_template.partition("://")
    if "/" in path_part:
        _, _, path_part = path_part.partition("/")
    segments = [segment for segment in path_part.split("/") if segment]
    for segment in reversed(segments):
        if not segment.startswith("{"):
            return segment
    return None


class _PromptFormatDict(dict[str, str]):
    """Return angle-bracket placeholders for missing prompt arguments."""

    def __missing__(self, key: str) -> str:
        return f"<{key}>"
