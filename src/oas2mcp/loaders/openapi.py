"""OpenAPI loading helpers.

Purpose:
    Load OpenAPI specifications from URLs, local files, or raw text into plain
    Python dictionaries.

Design:
    - Avoid runtime dependence on LangChain's ``OpenAPISpec`` parser for now.
    - Parse JSON first, then fall back to YAML.
    - Return plain dictionaries so the normalization layer can remain stable.
    - Provide backward-compatible helper names during the transition away from
      LangChain's ``OpenAPISpec`` path.

Examples:
    .. code-block:: python

        from oas2mcp.loaders.openapi import load_openapi_spec_dict_from_url

        spec_dict = load_openapi_spec_dict_from_url(
            "https://petstore3.swagger.io/api/v3/openapi.json",
        )
        print(spec_dict["openapi"])
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import yaml

_OPENAPI_TEXT_PREFIXES: tuple[str, ...] = (
    "{",
    "openapi:",
    "swagger:",
    "info:",
    "paths:",
)


def load_openapi_spec_dict_from_url(
    url: str,
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Load an OpenAPI specification dictionary from a URL.

    Args:
        url: The URL of the OpenAPI specification.
        timeout: Request timeout in seconds.

    Returns:
        The parsed OpenAPI specification as a plain dictionary.

    Raises:
        httpx.HTTPError: If the request fails.
        ValueError: If the response body is empty or cannot be parsed.

    Examples:
        .. code-block:: python

            spec_dict = load_openapi_spec_dict_from_url(
                "https://petstore3.swagger.io/api/v3/openapi.json",
            )
    """
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        response = client.get(url)
        response.raise_for_status()
        text = response.text

    return load_openapi_spec_dict_from_text(text)


def load_openapi_spec_dict_from_text(text: str) -> dict[str, Any]:
    """Load an OpenAPI specification dictionary from raw text.

    Args:
        text: Raw JSON or YAML OpenAPI text.

    Returns:
        The parsed OpenAPI specification as a plain dictionary.

    Raises:
        ValueError: If the text is empty or cannot be parsed into a dictionary.

    Examples:
        .. code-block:: python

            spec_dict = load_openapi_spec_dict_from_text(
                '{"openapi":"3.1.0","info":{"title":"A","version":"1"},"paths":{}}'
            )
    """
    if not text.strip():
        raise ValueError("OpenAPI text was empty.")

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise ValueError("Failed to parse OpenAPI text as JSON or YAML.") from exc

    if not isinstance(data, dict):
        raise ValueError("Parsed OpenAPI content was not a dictionary.")

    return normalize_api_description_dict(data)


def load_openapi_spec_dict_from_file(
    path: str | Path,
    *,
    encoding: str = "utf-8",
) -> dict[str, Any]:
    """Load an OpenAPI specification dictionary from a local file.

    Args:
        path: The file path to the OpenAPI specification.
        encoding: Text encoding used when reading the file.

    Returns:
        The parsed OpenAPI specification as a plain dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or cannot be parsed.

    Examples:
        .. code-block:: python

            spec_dict = load_openapi_spec_dict_from_file("openapi.json")
    """
    resolved_path = Path(path).expanduser().resolve()
    text = resolved_path.read_text(encoding=encoding)
    return load_openapi_spec_dict_from_text(text)


def load_openapi_spec_dict(
    source: str | Path,
    *,
    timeout: float = 30.0,
    encoding: str = "utf-8",
) -> dict[str, Any]:
    """Load an OpenAPI-compatible specification from a URL, file, or raw text.

    Args:
        source: URL, local file path, ``file://`` URI, or raw JSON/YAML text.
        timeout: Request timeout used for URL loading.
        encoding: Text encoding used when reading local files.

    Returns:
        The parsed specification as a plain dictionary.

    Raises:
        FileNotFoundError: If the source looks like a local file but is missing.
        ValueError: If the source cannot be parsed as JSON or YAML.

    Examples:
        .. code-block:: python

            spec_dict = load_openapi_spec_dict("openapi.yaml")
            spec_dict = load_openapi_spec_dict("https://example.com/openapi.json")
    """
    if isinstance(source, Path):
        return load_openapi_spec_dict_from_file(source, encoding=encoding)

    stripped = source.strip()
    if _looks_like_http_url(stripped):
        return load_openapi_spec_dict_from_url(stripped, timeout=timeout)

    if stripped.startswith("file://"):
        return load_openapi_spec_dict_from_file(
            Path(urlparse(stripped).path),
            encoding=encoding,
        )

    candidate_path = Path(stripped).expanduser()
    if candidate_path.exists():
        return load_openapi_spec_dict_from_file(candidate_path, encoding=encoding)

    if _looks_like_openapi_text(stripped):
        return load_openapi_spec_dict_from_text(stripped)

    if _looks_like_missing_spec_file(stripped):
        raise FileNotFoundError(f"OpenAPI source file was not found: {source!r}")

    raise ValueError(
        "OpenAPI source must be a URL, local file, file:// URI, or raw JSON/YAML text."
    )


def normalize_api_description_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize common API-description variants into an OpenAPI-style mapping.

    Args:
        data: Parsed JSON/YAML API description.

    Returns:
        A dictionary shaped like an OpenAPI document.

    Raises:
        ValueError: If the document is not an OpenAPI-style mapping.
    """
    if "openapi" in data:
        return data

    swagger_version = data.get("swagger")
    if isinstance(swagger_version, str) and swagger_version.startswith("2."):
        return _convert_swagger2_to_openapi(data)

    raise ValueError(
        "API description must declare either an 'openapi' version or a Swagger 'swagger: 2.x' version."
    )


def dump_openapi_spec(spec: Any) -> dict[str, Any]:
    """Convert a spec-like object into a plain dictionary.

    Args:
        spec: A plain dictionary or model-like object.

    Returns:
        A plain dictionary representation of the spec.

    Raises:
        TypeError: If ``spec`` cannot be converted into a dictionary.

    Examples:
        .. code-block:: python

            data = dump_openapi_spec({"openapi": "3.1.0"})
            assert data["openapi"] == "3.1.0"
    """
    if isinstance(spec, dict):
        return dict(spec)

    if hasattr(spec, "model_dump"):
        dumped = spec.model_dump()
        if isinstance(dumped, dict):
            return dumped

    if hasattr(spec, "dict"):
        dumped = spec.dict()
        if isinstance(dumped, dict):
            return dumped

    raise TypeError("OpenAPI spec could not be converted into a dictionary.")


def _looks_like_http_url(value: str) -> bool:
    """Return whether a string looks like an HTTP(S) URL."""
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _looks_like_missing_spec_file(value: str) -> bool:
    """Return whether a string looks like a spec file path that does not exist."""
    suffixes = (".json", ".yaml", ".yml")
    normalized = value.lower()
    if normalized.endswith(suffixes):
        return True
    return "/" in value or value.startswith(".") or value.startswith("~")


def _looks_like_openapi_text(value: str) -> bool:
    """Return whether a string looks like raw JSON or YAML API description text."""
    lowered = value.lstrip().lower()
    if "\n" in value or "\r" in value:
        return True
    return any(lowered.startswith(prefix) for prefix in _OPENAPI_TEXT_PREFIXES)


def _convert_swagger2_to_openapi(swagger_spec: dict[str, Any]) -> dict[str, Any]:
    """Convert a Swagger 2.0 document into an OpenAPI 3.x-compatible mapping."""
    openapi_spec: dict[str, Any] = {
        "openapi": "3.0.3",
        "info": dict(swagger_spec.get("info") or {}),
        "paths": _convert_swagger2_paths(swagger_spec),
    }

    servers = _build_swagger2_servers(swagger_spec)
    if servers:
        openapi_spec["servers"] = servers

    tags = swagger_spec.get("tags")
    if tags is not None:
        openapi_spec["tags"] = tags

    security = swagger_spec.get("security")
    if security is not None:
        openapi_spec["security"] = security

    components = _convert_swagger2_components(swagger_spec)
    if components:
        openapi_spec["components"] = components

    return openapi_spec


def _build_swagger2_servers(swagger_spec: dict[str, Any]) -> list[dict[str, str]]:
    """Build OpenAPI-style ``servers`` entries from Swagger 2 host metadata."""
    host = swagger_spec.get("host")
    if not isinstance(host, str) or not host.strip():
        return []

    base_path = swagger_spec.get("basePath")
    normalized_base_path = ""
    if isinstance(base_path, str) and base_path.strip():
        normalized_base_path = (
            base_path if base_path.startswith("/") else f"/{base_path}"
        )

    schemes = swagger_spec.get("schemes")
    if not isinstance(schemes, list) or not schemes:
        schemes = ["https"]

    servers: list[dict[str, str]] = []
    for scheme in schemes:
        if not isinstance(scheme, str) or not scheme.strip():
            continue
        servers.append({"url": f"{scheme}://{host}{normalized_base_path}"})
    return servers


def _convert_swagger2_components(swagger_spec: dict[str, Any]) -> dict[str, Any]:
    """Convert Swagger 2 reusable sections into OpenAPI ``components``."""
    components: dict[str, Any] = {}

    definitions = swagger_spec.get("definitions")
    if isinstance(definitions, dict) and definitions:
        components["schemas"] = definitions

    parameters = swagger_spec.get("parameters")
    if isinstance(parameters, dict) and parameters:
        components["parameters"] = parameters

    responses = swagger_spec.get("responses")
    if isinstance(responses, dict) and responses:
        components["responses"] = {
            name: _convert_swagger2_response(
                response,
                produces=_collect_media_types(
                    swagger_spec.get("produces"), "application/json"
                ),
            )
            for name, response in responses.items()
        }

    security_definitions = swagger_spec.get("securityDefinitions")
    if isinstance(security_definitions, dict) and security_definitions:
        components["securitySchemes"] = {
            name: _convert_swagger2_security_scheme(scheme)
            for name, scheme in security_definitions.items()
        }

    return components


def _convert_swagger2_paths(swagger_spec: dict[str, Any]) -> dict[str, Any]:
    """Convert Swagger 2 path items into OpenAPI 3 path items."""
    raw_paths = swagger_spec.get("paths")
    if not isinstance(raw_paths, dict):
        return {}

    default_consumes = _collect_media_types(
        swagger_spec.get("consumes"),
        "application/json",
    )
    default_produces = _collect_media_types(
        swagger_spec.get("produces"),
        "application/json",
    )

    converted_paths: dict[str, Any] = {}
    for path, raw_path_item in raw_paths.items():
        if not isinstance(raw_path_item, dict):
            continue

        path_item = dict(raw_path_item)
        path_level_consumes = _collect_media_types(
            path_item.get("consumes"),
            default_consumes[0],
        )
        path_level_produces = _collect_media_types(
            path_item.get("produces"),
            default_produces[0],
        )

        converted_path_item: dict[str, Any] = {}
        for key, value in path_item.items():
            lowered_key = str(key).lower()
            if lowered_key in {
                "get",
                "post",
                "put",
                "patch",
                "delete",
                "options",
                "head",
                "trace",
            }:
                converted_path_item[lowered_key] = _convert_swagger2_operation(
                    value,
                    consumes=(
                        _collect_media_types(
                            getattr(value, "get", lambda *_: None)("consumes"),
                            path_level_consumes[0],
                        )
                        if isinstance(value, dict)
                        else path_level_consumes
                    ),
                    produces=(
                        _collect_media_types(
                            getattr(value, "get", lambda *_: None)("produces"),
                            path_level_produces[0],
                        )
                        if isinstance(value, dict)
                        else path_level_produces
                    ),
                )
            elif lowered_key not in {"consumes", "produces", "swagger"}:
                converted_path_item[key] = value

        converted_paths[str(path)] = converted_path_item

    return converted_paths


def _convert_swagger2_operation(
    raw_operation: Any,
    *,
    consumes: list[str],
    produces: list[str],
) -> dict[str, Any]:
    """Convert one Swagger 2 operation object."""
    operation = dict(raw_operation) if isinstance(raw_operation, dict) else {}

    raw_parameters = operation.get("parameters")
    parameters = raw_parameters if isinstance(raw_parameters, list) else []
    remaining_parameters: list[Any] = []
    body_parameters: list[dict[str, Any]] = []
    form_parameters: list[dict[str, Any]] = []

    for parameter in parameters:
        if not isinstance(parameter, dict):
            remaining_parameters.append(parameter)
            continue

        location = parameter.get("in")
        if location == "body":
            body_parameters.append(parameter)
            continue
        if location == "formData":
            form_parameters.append(parameter)
            continue
        remaining_parameters.append(parameter)

    converted = {
        key: value
        for key, value in operation.items()
        if key not in {"parameters", "consumes", "produces"}
    }
    converted["parameters"] = remaining_parameters

    request_body = _build_swagger2_request_body(
        body_parameters=body_parameters,
        form_parameters=form_parameters,
        consumes=consumes,
    )
    if request_body is not None:
        converted["requestBody"] = request_body

    responses = operation.get("responses")
    if isinstance(responses, dict):
        converted["responses"] = {
            status_code: _convert_swagger2_response(response, produces=produces)
            for status_code, response in responses.items()
        }

    return converted


def _build_swagger2_request_body(
    *,
    body_parameters: list[dict[str, Any]],
    form_parameters: list[dict[str, Any]],
    consumes: list[str],
) -> dict[str, Any] | None:
    """Build an OpenAPI 3 ``requestBody`` from Swagger 2 parameters."""
    if body_parameters:
        body_parameter = body_parameters[0]
        schema = (
            body_parameter.get("schema") if isinstance(body_parameter, dict) else None
        )
        content = {
            media_type: {"schema": dict(schema) if isinstance(schema, dict) else {}}
            for media_type in consumes
        }
        return {
            "required": bool(body_parameter.get("required")),
            "description": body_parameter.get("description"),
            "content": content,
        }

    if not form_parameters:
        return None

    required = [
        parameter["name"]
        for parameter in form_parameters
        if isinstance(parameter, dict)
        and isinstance(parameter.get("name"), str)
        and bool(parameter.get("required"))
    ]
    properties: dict[str, Any] = {}
    has_file_param = False

    for parameter in form_parameters:
        if not isinstance(parameter, dict):
            continue
        name = parameter.get("name")
        if not isinstance(name, str) or not name:
            continue

        schema: dict[str, Any] = {
            key: value
            for key, value in parameter.items()
            if key
            in {
                "type",
                "format",
                "items",
                "enum",
                "default",
                "description",
            }
        }
        if schema.get("type") == "file":
            has_file_param = True
            schema["type"] = "string"
            schema["format"] = "binary"
        properties[name] = schema

    content_type = "multipart/form-data" if has_file_param else consumes[0]
    return {
        "required": bool(required),
        "content": {
            content_type: {
                "schema": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }
            }
        },
    }


def _convert_swagger2_response(
    raw_response: Any,
    *,
    produces: list[str],
) -> dict[str, Any]:
    """Convert a Swagger 2 response object into OpenAPI 3-style content."""
    response = dict(raw_response) if isinstance(raw_response, dict) else {}
    schema = response.pop("schema", None)
    if isinstance(schema, dict):
        response["content"] = {
            media_type: {"schema": dict(schema)} for media_type in produces
        }
    return response


def _convert_swagger2_security_scheme(raw_scheme: Any) -> dict[str, Any]:
    """Convert a Swagger 2 security scheme to an OpenAPI 3-compatible shape."""
    scheme = dict(raw_scheme) if isinstance(raw_scheme, dict) else {}
    scheme_type = scheme.get("type")

    if scheme_type == "basic":
        return {
            "type": "http",
            "scheme": "basic",
            **{key: value for key, value in scheme.items() if key not in {"type"}},
        }

    if scheme_type == "oauth2":
        flow = scheme.get("flow")
        scopes = dict(scheme.get("scopes") or {})
        flow_name = {
            "implicit": "implicit",
            "password": "password",
            "application": "clientCredentials",
            "accessCode": "authorizationCode",
        }.get(str(flow), "clientCredentials")
        flow_payload: dict[str, Any] = {"scopes": scopes}
        if scheme.get("authorizationUrl"):
            flow_payload["authorizationUrl"] = scheme["authorizationUrl"]
        if scheme.get("tokenUrl"):
            flow_payload["tokenUrl"] = scheme["tokenUrl"]

        converted = {
            key: value
            for key, value in scheme.items()
            if key
            not in {
                "flow",
                "authorizationUrl",
                "tokenUrl",
                "scopes",
            }
        }
        converted["flows"] = {flow_name: flow_payload}
        return converted

    return scheme


def _collect_media_types(raw_media_types: Any, default: str) -> list[str]:
    """Normalize media type lists with a deterministic default."""
    if isinstance(raw_media_types, list):
        collected = [
            media_type
            for media_type in raw_media_types
            if isinstance(media_type, str) and media_type.strip()
        ]
        if collected:
            return collected
    return [default]


# ---------------------------------------------------------------------------
# Backward-compatible aliases
# ---------------------------------------------------------------------------


def load_openapi_spec_from_url(
    url: str,
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Backward-compatible alias for URL-based spec loading."""
    return load_openapi_spec_dict_from_url(url, timeout=timeout)


def load_openapi_spec_from_text(text: str) -> dict[str, Any]:
    """Backward-compatible alias for text-based spec loading."""
    return load_openapi_spec_dict_from_text(text)


def load_openapi_spec_from_file(
    path: str | Path,
    *,
    encoding: str = "utf-8",
) -> dict[str, Any]:
    """Backward-compatible alias for file-based spec loading."""
    return load_openapi_spec_dict_from_file(path, encoding=encoding)


def load_openapi_spec(
    source: str | Path,
    *,
    timeout: float = 30.0,
    encoding: str = "utf-8",
) -> dict[str, Any]:
    """Backward-compatible alias for generic spec loading."""
    return load_openapi_spec_dict(
        source,
        timeout=timeout,
        encoding=encoding,
    )
