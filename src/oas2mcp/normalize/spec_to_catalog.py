"""OpenAPI-to-catalog normalization helpers.

Purpose:
    Convert parsed OpenAPI data into the normalized ``ApiCatalog`` model used by
    ``oas2mcp``.

Design:
    - Accept either LangChain ``OpenAPISpec`` objects or plain dictionaries.
    - Resolve relative server URLs against the original source URI.
    - Flatten OpenAPI path items into reusable normalized operations.
    - Preserve raw fragments where useful for later inspection or enrichment.
    - Prefer normalized model field names over alias names during model
      construction to keep Python call sites valid and readable.

Examples:
    .. code-block:: python

        from oas2mcp.loaders import load_openapi_spec_from_url
        from oas2mcp.normalize import openapi_spec_to_catalog

        source_uri = "https://petstore3.swagger.io/api/v3/openapi.json"
        spec = load_openapi_spec_from_url(source_uri)
        catalog = openapi_spec_to_catalog(spec, source_uri=source_uri)

        print(catalog.name)
        print(catalog.operation_count)
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urljoin, urlparse

from langchain_community.utilities.openapi import OpenAPISpec

from oas2mcp.loaders.openapi import dump_openapi_spec
from oas2mcp.models.normalized import (
    ApiCatalog,
    ApiContact,
    ApiInfo,
    ApiLicense,
    ApiMediaType,
    ApiOperation,
    ApiParameter,
    ApiPathItem,
    ApiRequestBody,
    ApiResponse,
    ApiSecurityRequirement,
    ApiSecurityScheme,
    ApiServer,
    ApiTag,
)

_HTTP_METHODS: tuple[str, ...] = (
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "options",
    "head",
    "trace",
)


def spec_dict_to_catalog(
    spec_dict: Mapping[str, Any], *, source_uri: str
) -> ApiCatalog:
    """Normalize a dumped OpenAPI specification into an ``ApiCatalog``.

    Args:
        spec_dict: A plain-Python OpenAPI specification mapping.
        source_uri: The URI from which the spec originated. This is used for
            source tracking and for resolving relative server URLs.

    Returns:
        A normalized ``ApiCatalog``.

    Raises:
        ValueError: If ``source_uri`` is empty.

    Examples:
        .. code-block:: python

            from oas2mcp.normalize import spec_dict_to_catalog

            catalog = spec_dict_to_catalog(
                {
                    "openapi": "3.1.0",
                    "info": {"title": "Example API", "version": "1.0.0"},
                    "paths": {},
                },
                source_uri="https://example.com/openapi.json",
            )
    """
    if not source_uri.strip():
        raise ValueError("source_uri cannot be empty.")

    resolved_spec = dict(spec_dict)
    info_mapping = _as_mapping(resolved_spec.get("info"))
    components_mapping = _as_mapping(resolved_spec.get("components"))

    name = _infer_catalog_name(info_mapping, source_uri)
    info = _normalize_info(info_mapping)
    servers = _normalize_servers(resolved_spec.get("servers"), source_uri=source_uri)
    tags = _normalize_tags(resolved_spec.get("tags"))
    security_schemes = _normalize_security_schemes(
        components_mapping.get("securitySchemes"),
    )
    global_security = _normalize_security_requirements(resolved_spec.get("security"))
    component_counts = _build_component_counts(components_mapping)

    paths, operations = _normalize_paths(
        resolved_spec.get("paths"),
        global_security=global_security,
    )

    return ApiCatalog(
        name=name,
        source_uri=source_uri,
        openapi_version=_as_optional_str(resolved_spec.get("openapi")),
        info=info,
        servers=servers,
        tags=tags,
        security_schemes=security_schemes,
        global_security=global_security,
        paths=paths,
        operations=operations,
        component_counts=component_counts,
        raw_spec=resolved_spec,
    )


def openapi_spec_to_catalog(spec: OpenAPISpec, *, source_uri: str) -> ApiCatalog:
    """Normalize a LangChain ``OpenAPISpec`` into an ``ApiCatalog``.

    Args:
        spec: The parsed LangChain OpenAPI spec.
        source_uri: The URI from which the spec originated.

    Returns:
        A normalized ``ApiCatalog``.

    Raises:
        ValueError: If ``source_uri`` is empty.

    Examples:
        .. code-block:: python

            from oas2mcp.loaders import load_openapi_spec_from_url
            from oas2mcp.normalize import openapi_spec_to_catalog

            source_uri = "https://petstore3.swagger.io/api/v3/openapi.json"
            spec = load_openapi_spec_from_url(source_uri)
            catalog = openapi_spec_to_catalog(spec, source_uri=source_uri)
    """
    spec_dict = dump_openapi_spec(spec)
    return spec_dict_to_catalog(spec_dict, source_uri=source_uri)


def _as_mapping(value: Any) -> dict[str, Any]:
    """Return a plain dictionary for mapping-like input.

    Args:
        value: The candidate mapping-like object.

    Returns:
        A plain dictionary when the input is mapping-like, otherwise an empty
        dictionary.

    Raises:
        None.

    Examples:
        .. code-block:: python

            assert _as_mapping({"a": 1}) == {"a": 1}
            assert _as_mapping(None) == {}
    """
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _as_sequence(value: Any) -> list[Any]:
    """Return a plain list for sequence-like input.

    Args:
        value: The candidate sequence-like object.

    Returns:
        A plain list when the input is sequence-like and not string-like,
        otherwise an empty list.

    Raises:
        None.

    Examples:
        .. code-block:: python

            assert _as_sequence([1, 2]) == [1, 2]
            assert _as_sequence("abc") == []
    """
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    return []


def _as_optional_str(value: Any) -> str | None:
    """Return a cleaned string or ``None``.

    Args:
        value: The candidate string value.

    Returns:
        A stripped string when the value is a non-empty string, otherwise
        ``None``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            assert _as_optional_str(" hello ") == "hello"
            assert _as_optional_str("") is None
    """
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return None


def _as_bool(value: Any) -> bool:
    """Return a normalized boolean.

    Args:
        value: The candidate value.

    Returns:
        The boolean interpretation of ``value``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            assert _as_bool(1) is True
            assert _as_bool(0) is False
    """
    return bool(value)


def _infer_catalog_name(info_mapping: Mapping[str, Any], source_uri: str) -> str:
    """Infer the catalog display name from ``info.title`` or the source host.

    Args:
        info_mapping: The normalized ``info`` mapping.
        source_uri: The original source URI.

    Returns:
        The inferred catalog name.

    Raises:
        None.

    Examples:
        .. code-block:: python

            name = _infer_catalog_name({"title": "Petstore"}, "https://example.com")
            assert name == "Petstore"
    """
    title = _as_optional_str(info_mapping.get("title"))
    if title is not None:
        return title

    parsed = urlparse(source_uri)
    if parsed.netloc:
        return parsed.netloc

    return "OpenAPI Catalog"


def _normalize_info(info_mapping: Mapping[str, Any]) -> ApiInfo | None:
    """Normalize the top-level OpenAPI ``info`` block.

    Args:
        info_mapping: The raw ``info`` mapping.

    Returns:
        A normalized ``ApiInfo`` when enough metadata exists, otherwise
        ``None``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            info = _normalize_info({"title": "API", "version": "1.0.0"})
            assert info is not None
    """
    title = _as_optional_str(info_mapping.get("title"))
    version = _as_optional_str(info_mapping.get("version"))

    if title is None or version is None:
        return None

    contact_mapping = _as_mapping(info_mapping.get("contact"))
    license_mapping = _as_mapping(info_mapping.get("license"))

    contact = (
        ApiContact(
            name=_as_optional_str(contact_mapping.get("name")),
            email=_as_optional_str(contact_mapping.get("email")),
            url=_as_optional_str(contact_mapping.get("url")),
        )
        if contact_mapping
        else None
    )

    license_info = (
        ApiLicense(
            name=_as_optional_str(license_mapping.get("name")) or "Unknown",
            identifier=_as_optional_str(license_mapping.get("identifier")),
            url=_as_optional_str(license_mapping.get("url")),
        )
        if license_mapping
        else None
    )

    return ApiInfo(
        title=title,
        version=version,
        summary=_as_optional_str(info_mapping.get("summary")),
        description=_as_optional_str(info_mapping.get("description")),
        terms_of_service=_as_optional_str(info_mapping.get("termsOfService")),
        contact=contact,
        license=license_info,
    )


def _normalize_servers(
    raw_servers: Any,
    *,
    source_uri: str,
) -> list[ApiServer]:
    """Normalize OpenAPI servers and resolve relative URLs.

    Args:
        raw_servers: The raw ``servers`` value from the spec.
        source_uri: The original source URI.

    Returns:
        A list of normalized ``ApiServer`` instances.

    Raises:
        None.

    Examples:
        .. code-block:: python

            servers = _normalize_servers(
                [{"url": "/api"}],
                source_uri="https://example.com/openapi.json",
            )
            assert servers[0].url == "https://example.com/api"
    """
    servers: list[ApiServer] = []

    for raw_server in _as_sequence(raw_servers):
        server_mapping = _as_mapping(raw_server)
        url = _as_optional_str(server_mapping.get("url"))
        if url is None:
            continue

        resolved_url = urljoin(source_uri, url)
        variables = _normalize_server_variables(server_mapping.get("variables"))

        servers.append(
            ApiServer(
                url=resolved_url,
                description=_as_optional_str(server_mapping.get("description")),
                variables=variables,
            )
        )

    if servers:
        return servers

    parsed = urlparse(source_uri)
    if parsed.scheme and parsed.netloc:
        default_url = f"{parsed.scheme}://{parsed.netloc}"
    else:
        default_url = source_uri

    return [ApiServer(url=default_url, description="Derived from source URI")]


def _normalize_server_variables(raw_variables: Any) -> dict[str, dict[str, Any]]:
    """Normalize server variables into plain dictionaries.

    Args:
        raw_variables: The raw server variables mapping.

    Returns:
        A normalized mapping of variable names to metadata dictionaries.

    Raises:
        None.

    Examples:
        .. code-block:: python

            variables = _normalize_server_variables(
                {"env": {"default": "prod"}}
            )
            assert variables["env"]["default"] == "prod"
    """
    variables: dict[str, dict[str, Any]] = {}

    for name, raw_metadata in _as_mapping(raw_variables).items():
        variables[str(name)] = dict(_as_mapping(raw_metadata))

    return variables


def _normalize_tags(raw_tags: Any) -> list[ApiTag]:
    """Normalize top-level OpenAPI tags.

    Args:
        raw_tags: The raw ``tags`` value from the spec.

    Returns:
        A list of normalized ``ApiTag`` instances.

    Raises:
        None.

    Examples:
        .. code-block:: python

            tags = _normalize_tags([{"name": "pets"}])
            assert tags[0].name == "pets"
    """
    tags: list[ApiTag] = []

    for raw_tag in _as_sequence(raw_tags):
        tag_mapping = _as_mapping(raw_tag)
        name = _as_optional_str(tag_mapping.get("name"))
        if name is None:
            continue

        external_docs_mapping = _as_mapping(tag_mapping.get("externalDocs"))

        tags.append(
            ApiTag(
                name=name,
                description=_as_optional_str(tag_mapping.get("description")),
                external_docs_description=_as_optional_str(
                    external_docs_mapping.get("description")
                ),
                external_docs_url=_as_optional_str(external_docs_mapping.get("url")),
            )
        )

    return tags


def _normalize_security_schemes(raw_security_schemes: Any) -> list[ApiSecurityScheme]:
    """Normalize named security schemes from ``components.securitySchemes``.

    Args:
        raw_security_schemes: The raw security schemes mapping.

    Returns:
        A list of normalized ``ApiSecurityScheme`` instances.

    Raises:
        None.

    Examples:
        .. code-block:: python

            schemes = _normalize_security_schemes(
                {"apiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"}}
            )
            assert schemes[0].name == "apiKeyAuth"
    """
    schemes: list[ApiSecurityScheme] = []

    for scheme_name, raw_scheme in _as_mapping(raw_security_schemes).items():
        scheme_mapping = _as_mapping(raw_scheme)
        scheme_type = _as_optional_str(scheme_mapping.get("type"))
        if scheme_type is None:
            continue

        schemes.append(
            ApiSecurityScheme(
                name=str(scheme_name),
                type=scheme_type,
                description=_as_optional_str(scheme_mapping.get("description")),
                scheme=_as_optional_str(scheme_mapping.get("scheme")),
                bearer_format=_as_optional_str(scheme_mapping.get("bearerFormat")),
                location=_as_optional_str(scheme_mapping.get("in")),
                parameter_name=_as_optional_str(scheme_mapping.get("name")),
                open_id_connect_url=_as_optional_str(
                    scheme_mapping.get("openIdConnectUrl")
                ),
                flows=_as_mapping(scheme_mapping.get("flows")),
            )
        )

    return schemes


def _normalize_security_requirements(
    raw_requirements: Any,
) -> list[ApiSecurityRequirement]:
    """Normalize OpenAPI security requirement arrays.

    Args:
        raw_requirements: The raw security requirement list.

    Returns:
        A list of normalized ``ApiSecurityRequirement`` instances.

    Raises:
        None.

    Examples:
        .. code-block:: python

            requirements = _normalize_security_requirements([{"bearerAuth": []}])
            assert requirements[0].scheme_names == ["bearerAuth"]
    """
    requirements: list[ApiSecurityRequirement] = []

    for raw_requirement in _as_sequence(raw_requirements):
        requirement_mapping = _as_mapping(raw_requirement)
        if not requirement_mapping:
            requirements.append(ApiSecurityRequirement(scheme_names=[]))
            continue

        requirements.append(
            ApiSecurityRequirement(
                scheme_names=[str(key) for key in requirement_mapping.keys()],
            )
        )

    return requirements


def _build_component_counts(components_mapping: Mapping[str, Any]) -> dict[str, int]:
    """Build simple counts for common OpenAPI component sections.

    Args:
        components_mapping: The raw ``components`` mapping.

    Returns:
        A mapping of section names to simple counts.

    Raises:
        None.

    Examples:
        .. code-block:: python

            counts = _build_component_counts({"schemas": {"A": {}, "B": {}}})
            assert counts["schemas"] == 2
    """
    section_names = (
        "schemas",
        "responses",
        "parameters",
        "examples",
        "requestBodies",
        "headers",
        "securitySchemes",
        "links",
        "callbacks",
    )

    counts: dict[str, int] = {}
    for section_name in section_names:
        counts[section_name] = len(_as_mapping(components_mapping.get(section_name)))

    return counts


def _normalize_paths(
    raw_paths: Any,
    *,
    global_security: list[ApiSecurityRequirement],
) -> tuple[list[ApiPathItem], list[ApiOperation]]:
    """Normalize OpenAPI paths into path items and flattened operations.

    Args:
        raw_paths: The raw ``paths`` mapping.
        global_security: The normalized top-level security requirements.

    Returns:
        A tuple of ``(path_items, operations)``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            path_items, operations = _normalize_paths(
                {"/pets": {"get": {"responses": {"200": {"description": "ok"}}}}},
                global_security=[],
            )
            assert len(path_items) == 1
            assert len(operations) == 1
    """
    path_items: list[ApiPathItem] = []
    operations: list[ApiOperation] = []

    for raw_path, raw_path_item in _as_mapping(raw_paths).items():
        path = _normalize_path_string(str(raw_path))
        path_item_mapping = _as_mapping(raw_path_item)
        path_parameters = _normalize_parameters(path_item_mapping.get("parameters"))

        path_operations: list[ApiOperation] = []
        for method_name in _HTTP_METHODS:
            raw_operation = path_item_mapping.get(method_name)
            operation_mapping = _as_mapping(raw_operation)
            if not operation_mapping:
                continue

            operation = _normalize_operation(
                method=method_name,
                path=path,
                operation_mapping=operation_mapping,
                path_parameters=path_parameters,
                global_security=global_security,
            )
            path_operations.append(operation)
            operations.append(operation)

        path_items.append(
            ApiPathItem(
                path=path,
                parameters=path_parameters,
                operations=path_operations,
            )
        )

    return path_items, operations


def _normalize_operation(
    *,
    method: str,
    path: str,
    operation_mapping: Mapping[str, Any],
    path_parameters: list[ApiParameter],
    global_security: list[ApiSecurityRequirement],
) -> ApiOperation:
    """Normalize a single OpenAPI operation.

    Args:
        method: The lowercase HTTP method name.
        path: The normalized OpenAPI path.
        operation_mapping: The raw operation mapping.
        path_parameters: Parameters inherited from the path item.
        global_security: The normalized top-level security requirements.

    Returns:
        A normalized ``ApiOperation``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            operation = _normalize_operation(
                method="get",
                path="/pets",
                operation_mapping={"responses": {"200": {"description": "ok"}}},
                path_parameters=[],
                global_security=[],
            )
            assert operation.method == "GET"
    """
    operation_parameters = _normalize_parameters(operation_mapping.get("parameters"))
    merged_parameters = [*path_parameters, *operation_parameters]

    request_body_mapping = _as_mapping(operation_mapping.get("requestBody"))
    request_body = (
        _normalize_request_body(request_body_mapping) if request_body_mapping else None
    )

    responses = _normalize_responses(operation_mapping.get("responses"))
    operation_security = _normalize_security_requirements(
        operation_mapping.get("security")
    )
    external_docs_mapping = _as_mapping(operation_mapping.get("externalDocs"))

    return ApiOperation(
        method=method,
        path=path,
        operation_id=_as_optional_str(operation_mapping.get("operationId")),
        summary=_as_optional_str(operation_mapping.get("summary")),
        description=_as_optional_str(operation_mapping.get("description")),
        tags=[
            str(tag)
            for tag in _as_sequence(operation_mapping.get("tags"))
            if isinstance(tag, str) and tag.strip()
        ],
        parameters=_deduplicate_parameters(merged_parameters),
        request_body=request_body,
        responses=responses,
        security=operation_security if operation_security else list(global_security),
        deprecated=_as_bool(operation_mapping.get("deprecated")),
        external_docs_description=_as_optional_str(
            external_docs_mapping.get("description")
        ),
        external_docs_url=_as_optional_str(external_docs_mapping.get("url")),
        raw_operation=dict(operation_mapping),
    )


def _normalize_parameters(raw_parameters: Any) -> list[ApiParameter]:
    """Normalize OpenAPI parameters.

    Args:
        raw_parameters: The raw parameters list.

    Returns:
        A list of normalized ``ApiParameter`` instances.

    Raises:
        None.

    Examples:
        .. code-block:: python

            params = _normalize_parameters(
                [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}]
            )
            assert params[0].name == "id"
    """
    parameters: list[ApiParameter] = []

    for raw_parameter in _as_sequence(raw_parameters):
        parameter_mapping = _as_mapping(raw_parameter)
        if not parameter_mapping:
            continue

        name = _as_optional_str(parameter_mapping.get("name"))
        location = _as_optional_str(parameter_mapping.get("in"))
        if name is None or location is None:
            continue

        schema_mapping = _as_mapping(parameter_mapping.get("schema"))
        enum_values = list(_as_sequence(schema_mapping.get("enum")))

        parameters.append(
            ApiParameter(
                name=name,
                location=location,
                required=_as_bool(parameter_mapping.get("required")),
                description=_as_optional_str(parameter_mapping.get("description")),
                schema_type=_as_optional_str(schema_mapping.get("type")),
                schema_format=_as_optional_str(schema_mapping.get("format")),
                default=schema_mapping.get("default"),
                enum_values=enum_values,
                raw_schema=schema_mapping,
            )
        )

    return parameters


def _deduplicate_parameters(parameters: list[ApiParameter]) -> list[ApiParameter]:
    """Deduplicate parameters by ``(location, name)`` while preserving order.

    Args:
        parameters: The candidate parameters.

    Returns:
        A de-duplicated parameter list.

    Raises:
        None.

    Examples:
        .. code-block:: python

            parameter = ApiParameter(name="id", location="path")
            result = _deduplicate_parameters([parameter, parameter])
            assert len(result) == 1
    """
    seen: set[tuple[str, str]] = set()
    deduplicated: list[ApiParameter] = []

    for parameter in parameters:
        key = (parameter.location, parameter.name)
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(parameter)

    return deduplicated


def _normalize_request_body(request_body_mapping: Mapping[str, Any]) -> ApiRequestBody:
    """Normalize an OpenAPI request body.

    Args:
        request_body_mapping: The raw request body mapping.

    Returns:
        A normalized ``ApiRequestBody``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            body = _normalize_request_body({"required": True, "content": {}})
            assert body.required is True
    """
    return ApiRequestBody(
        required=_as_bool(request_body_mapping.get("required")),
        description=_as_optional_str(request_body_mapping.get("description")),
        media_types=_normalize_media_types(request_body_mapping.get("content")),
    )


def _normalize_responses(raw_responses: Any) -> list[ApiResponse]:
    """Normalize OpenAPI responses.

    Args:
        raw_responses: The raw responses mapping.

    Returns:
        A list of normalized ``ApiResponse`` instances.

    Raises:
        None.

    Examples:
        .. code-block:: python

            responses = _normalize_responses({"200": {"description": "ok"}})
            assert responses[0].status_code == "200"
    """
    responses: list[ApiResponse] = []

    for status_code, raw_response in _as_mapping(raw_responses).items():
        response_mapping = _as_mapping(raw_response)
        if not response_mapping:
            continue

        responses.append(
            ApiResponse(
                status_code=str(status_code),
                description=_as_optional_str(response_mapping.get("description")),
                media_types=_normalize_media_types(response_mapping.get("content")),
                headers=_as_mapping(response_mapping.get("headers")),
            )
        )

    return responses


def _normalize_media_types(raw_content: Any) -> list[ApiMediaType]:
    """Normalize media-type entries from request or response content maps.

    Args:
        raw_content: The raw OpenAPI content mapping.

    Returns:
        A list of normalized ``ApiMediaType`` instances.

    Raises:
        None.

    Examples:
        .. code-block:: python

            media_types = _normalize_media_types(
                {"application/json": {"schema": {"type": "object"}}}
            )
            assert media_types[0].content_type == "application/json"
    """
    media_types: list[ApiMediaType] = []

    for content_type, raw_media_type in _as_mapping(raw_content).items():
        media_mapping = _as_mapping(raw_media_type)
        schema_mapping = _as_mapping(media_mapping.get("schema"))

        media_types.append(
            ApiMediaType(
                content_type=str(content_type),
                schema_ref=_as_optional_str(schema_mapping.get("$ref")),
                schema_type=_as_optional_str(schema_mapping.get("type")),
                example=media_mapping.get("example"),
                examples=_as_mapping(media_mapping.get("examples")),
                raw_schema=schema_mapping,
            )
        )

    return media_types


def _normalize_path_string(value: str) -> str:
    """Normalize a path string to begin with ``/``.

    Args:
        value: The candidate path string.

    Returns:
        A normalized path string.

    Raises:
        None.

    Examples:
        .. code-block:: python

            assert _normalize_path_string("pets") == "/pets"
    """
    cleaned = value.strip()
    if not cleaned:
        return "/"
    if not cleaned.startswith("/"):
        return f"/{cleaned}"
    return cleaned
