"""Normalized OpenAPI models.

Purpose:
    Define stable, typed Pydantic models for the normalized internal view of
    an OpenAPI specification.

Design:
    - Flatten OpenAPI structures into reusable, agent-friendly models.
    - Preserve enough metadata for Rich rendering, inspection, and later MCP
      generation.
    - Use clean internal field names instead of OpenAPI alias names where the
      alias would be awkward or invalid in Python, such as ``in``.
    - Keep raw fragments available for debugging and future enrichment.

Examples:
    .. code-block:: python

        from oas2mcp.models.normalized import ApiCatalog, ApiOperation

        operation = ApiOperation(
            method="get",
            path="/pets/{petId}",
            operation_id="getPetById",
            summary="Fetch one pet",
        )

        catalog = ApiCatalog(
            name="Petstore",
            source_uri="https://petstore3.swagger.io/api/v3/openapi.json",
            operations=[operation],
        )
"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

HTTP_METHODS: tuple[str, ...] = (
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
    "HEAD",
    "TRACE",
)

__all__ = [
    "HTTP_METHODS",
    "NormalizedBaseModel",
    "ApiContact",
    "ApiLicense",
    "ApiInfo",
    "ApiServer",
    "ApiTag",
    "ApiSecurityRequirement",
    "ApiSecurityScheme",
    "ApiParameter",
    "ApiMediaType",
    "ApiRequestBody",
    "ApiResponse",
    "ApiOperation",
    "ApiPathItem",
    "ApiCatalog",
]


class NormalizedBaseModel(BaseModel):
    """Base model for normalized OpenAPI objects.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            class ExampleModel(NormalizedBaseModel):
                name: str
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )


class ApiContact(NormalizedBaseModel):
    """Contact metadata for an API.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            contact = ApiContact(
                name="API Support",
                email="support@example.com",
                url="https://example.com/support",
            )
    """

    name: str | None = None
    email: str | None = None
    url: str | None = None


class ApiLicense(NormalizedBaseModel):
    """License metadata for an API.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            license_info = ApiLicense(name="MIT")
    """

    name: str
    identifier: str | None = None
    url: str | None = None


class ApiInfo(NormalizedBaseModel):
    """Top-level API metadata.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            info = ApiInfo(
                title="Petstore",
                version="1.0.0",
                summary="Pet operations",
            )
    """

    title: str
    version: str
    summary: str | None = None
    description: str | None = None
    terms_of_service: str | None = None
    contact: ApiContact | None = None
    license: ApiLicense | None = None


class ApiServer(NormalizedBaseModel):
    """Resolved server definition.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            server = ApiServer(
                url="https://api.example.com",
                description="Production",
            )
    """

    url: str
    description: str | None = None
    variables: dict[str, dict[str, Any]] = Field(default_factory=dict)


class ApiTag(NormalizedBaseModel):
    """Normalized tag metadata.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            tag = ApiTag(
                name="pets",
                description="Operations about pets.",
            )
    """

    name: str
    description: str | None = None
    external_docs_description: str | None = None
    external_docs_url: str | None = None


class ApiSecurityRequirement(NormalizedBaseModel):
    """One normalized security requirement mapping.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            requirement = ApiSecurityRequirement(
                scheme_names=["bearerAuth"],
            )
    """

    scheme_names: list[str] = Field(default_factory=list)


class ApiSecurityScheme(NormalizedBaseModel):
    """One named security scheme.

    Design:
        ``name`` is the scheme identifier from ``components.securitySchemes``.
        ``parameter_name`` is the header/query/cookie parameter name used by
        some schemes such as API key auth.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            scheme = ApiSecurityScheme(
                name="apiKeyAuth",
                type="apiKey",
                location="header",
                parameter_name="X-API-Key",
            )
    """

    name: str
    type: str
    description: str | None = None
    scheme: str | None = None
    bearer_format: str | None = None
    location: str | None = None
    parameter_name: str | None = None
    open_id_connect_url: str | None = None
    flows: dict[str, Any] = Field(default_factory=dict)


class ApiParameter(NormalizedBaseModel):
    """Normalized operation parameter.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            parameter = ApiParameter(
                name="petId",
                location="path",
                required=True,
                schema_type="integer",
            )
    """

    name: str
    location: str
    required: bool = False
    description: str | None = None
    schema_type: str | None = None
    schema_format: str | None = None
    default: Any | None = None
    enum_values: list[Any] = Field(default_factory=list)
    raw_schema: dict[str, Any] = Field(default_factory=dict)

    @field_validator("location")
    @classmethod
    def validate_location(cls, value: str) -> str:
        """Validate a parameter location.

        Args:
            value: The parameter location.

        Returns:
            The validated location.

        Raises:
            ValueError: If the location is unsupported.

        Examples:
            .. code-block:: python

                ApiParameter(
                    name="petId",
                    location="path",
                )
        """
        allowed = {"path", "query", "header", "cookie"}
        if value not in allowed:
            raise ValueError(
                f"Unsupported parameter location {value!r}. Expected one of {sorted(allowed)}."
            )
        return value


class ApiMediaType(NormalizedBaseModel):
    """Normalized media type description.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            media = ApiMediaType(
                content_type="application/json",
                schema_type="object",
            )
    """

    content_type: str
    schema_ref: str | None = None
    schema_type: str | None = None
    example: Any | None = None
    examples: dict[str, Any] = Field(default_factory=dict)
    raw_schema: dict[str, Any] = Field(default_factory=dict)


class ApiRequestBody(NormalizedBaseModel):
    """Normalized request body definition.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            body = ApiRequestBody(
                required=True,
                media_types=[ApiMediaType(content_type="application/json")],
            )
    """

    required: bool = False
    description: str | None = None
    media_types: list[ApiMediaType] = Field(default_factory=list)


class ApiResponse(NormalizedBaseModel):
    """Normalized response definition.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            response = ApiResponse(
                status_code="200",
                description="Success",
            )
    """

    status_code: str
    description: str | None = None
    media_types: list[ApiMediaType] = Field(default_factory=list)
    headers: dict[str, Any] = Field(default_factory=dict)


class ApiOperation(NormalizedBaseModel):
    """One normalized HTTP operation.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            operation = ApiOperation(
                method="get",
                path="/pets/{petId}",
                operation_id="getPetById",
            )
    """

    method: str
    path: str
    operation_id: str | None = None
    summary: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    parameters: list[ApiParameter] = Field(default_factory=list)
    request_body: ApiRequestBody | None = None
    responses: list[ApiResponse] = Field(default_factory=list)
    security: list[ApiSecurityRequirement] = Field(default_factory=list)
    deprecated: bool = False
    external_docs_description: str | None = None
    external_docs_url: str | None = None
    raw_operation: dict[str, Any] = Field(default_factory=dict)

    _http_methods: ClassVar[set[str]] = set(HTTP_METHODS)

    @field_validator("method")
    @classmethod
    def normalize_method(cls, value: str) -> str:
        """Normalize and validate an HTTP method.

        Args:
            value: The input HTTP method.

        Returns:
            The normalized uppercase HTTP method.

        Raises:
            ValueError: If the method is unsupported.

        Examples:
            .. code-block:: python

                ApiOperation(
                    method="get",
                    path="/pets",
                )
        """
        normalized = value.upper()
        if normalized not in cls._http_methods:
            raise ValueError(
                f"Unsupported HTTP method {value!r}. Expected one of {sorted(cls._http_methods)}."
            )
        return normalized

    @field_validator("path")
    @classmethod
    def normalize_path(cls, value: str) -> str:
        """Normalize a path string.

        Args:
            value: The raw path string.

        Returns:
            The normalized path starting with ``/``.

        Raises:
            ValueError: If the path is empty.

        Examples:
            .. code-block:: python

                ApiOperation(
                    method="GET",
                    path="pets/{petId}",
                )
        """
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Operation path cannot be empty.")
        if not cleaned.startswith("/"):
            cleaned = f"/{cleaned}"
        return cleaned

    @computed_field
    @property
    def key(self) -> str:
        """Return a stable operation lookup key.

        Args:
            None.

        Returns:
            A ``METHOD path`` lookup key.

        Raises:
            None.

        Examples:
            .. code-block:: python

                operation = ApiOperation(method="GET", path="/pets")
                assert operation.key == "GET /pets"
        """
        return f"{self.method} {self.path}"

    @computed_field
    @property
    def is_mutating(self) -> bool:
        """Return whether the operation mutates remote state.

        Args:
            None.

        Returns:
            ``True`` for mutating HTTP methods.

        Raises:
            None.

        Examples:
            .. code-block:: python

                operation = ApiOperation(method="POST", path="/pets")
                assert operation.is_mutating is True
        """
        return self.method in {"POST", "PUT", "PATCH", "DELETE"}


class ApiPathItem(NormalizedBaseModel):
    """Normalized path item grouping multiple operations.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            item = ApiPathItem(
                path="/pets",
                operations=[],
            )
    """

    path: str
    parameters: list[ApiParameter] = Field(default_factory=list)
    operations: list[ApiOperation] = Field(default_factory=list)

    @field_validator("path")
    @classmethod
    def normalize_path(cls, value: str) -> str:
        """Normalize a path item path.

        Args:
            value: The raw path string.

        Returns:
            The normalized path string.

        Raises:
            ValueError: If the path is empty.

        Examples:
            .. code-block:: python

                ApiPathItem(path="/pets")
        """
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Path item path cannot be empty.")
        if not cleaned.startswith("/"):
            cleaned = f"/{cleaned}"
        return cleaned


class ApiCatalog(NormalizedBaseModel):
    """Top-level normalized API catalog.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            catalog = ApiCatalog(
                name="Petstore",
                source_uri="https://example.com/openapi.json",
            )
    """

    name: str
    source_uri: str
    openapi_version: str | None = None
    info: ApiInfo | None = None
    servers: list[ApiServer] = Field(default_factory=list)
    tags: list[ApiTag] = Field(default_factory=list)
    security_schemes: list[ApiSecurityScheme] = Field(default_factory=list)
    global_security: list[ApiSecurityRequirement] = Field(default_factory=list)
    paths: list[ApiPathItem] = Field(default_factory=list)
    operations: list[ApiOperation] = Field(default_factory=list)
    component_counts: dict[str, int] = Field(default_factory=dict)
    raw_spec: dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def operation_count(self) -> int:
        """Return the number of normalized operations.

        Args:
            None.

        Returns:
            The number of operations in the catalog.

        Raises:
            None.

        Examples:
            .. code-block:: python

                catalog = ApiCatalog(
                    name="Petstore",
                    source_uri="https://example.com/openapi.json",
                )
                assert catalog.operation_count == 0
        """
        return len(self.operations)

    @computed_field
    @property
    def tag_names(self) -> list[str]:
        """Return all tag names.

        Args:
            None.

        Returns:
            A list of tag names.

        Raises:
            None.

        Examples:
            .. code-block:: python

                catalog = ApiCatalog(
                    name="Petstore",
                    source_uri="https://example.com/openapi.json",
                )
                assert catalog.tag_names == []
        """
        return [tag.name for tag in self.tags]
