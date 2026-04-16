"""Naming helpers for normalized catalogs and MCP preparation.

Purpose:
    Create stable slugs, tool names, and resource URIs from normalized OpenAPI
    metadata.

Design:
    - Keep naming deterministic.
    - Prefer operation identifiers when available.
    - Fall back to method + path when ``operationId`` is missing.

Examples:
    .. code-block:: python

        slug = make_operation_slug(operation)
        tool_name = make_tool_name(catalog_name="petstore", operation=operation)
"""

from __future__ import annotations

import re

from oas2mcp.models.normalized import ApiOperation

_NON_ALNUM_PATTERN = re.compile(r"[^a-z0-9]+")
_DUP_DASH_PATTERN = re.compile(r"-+")


def slugify(value: str) -> str:
    """Convert a string into a simple slug.

    Args:
        value: The input string.

    Returns:
        A lowercase slug.

    Raises:
        None.

    Examples:
        .. code-block:: python

            assert slugify("Swagger Petstore - OpenAPI 3.0") == "swagger-petstore-openapi-3-0"
    """
    lowered = value.strip().lower()
    replaced = _NON_ALNUM_PATTERN.sub("-", lowered)
    collapsed = _DUP_DASH_PATTERN.sub("-", replaced).strip("-")
    return collapsed or "item"


def make_catalog_slug(catalog_name: str) -> str:
    """Create a stable catalog slug.

    Args:
        catalog_name: The catalog display name.

    Returns:
        The catalog slug.

    Raises:
        None.

    Examples:
        .. code-block:: python

            slug = make_catalog_slug("Swagger Petstore - OpenAPI 3.0")
    """
    return slugify(catalog_name)


def make_tag_slug(tag_name: str) -> str:
    """Create a stable tag slug.

    Args:
        tag_name: The tag name.

    Returns:
        The tag slug.

    Raises:
        None.

    Examples:
        .. code-block:: python

            slug = make_tag_slug("pet")
    """
    return slugify(tag_name)


def make_operation_slug(operation: ApiOperation) -> str:
    """Create a stable operation slug.

    Args:
        operation: The normalized API operation.

    Returns:
        The operation slug.

    Raises:
        None.

    Examples:
        .. code-block:: python

            slug = make_operation_slug(operation)
    """
    if operation.operation_id:
        return slugify(operation.operation_id)

    path_bits = (
        operation.path.strip("/").replace("/", "-").replace("{", "").replace("}", "")
    )
    return slugify(f"{operation.method.lower()}-{path_bits}")


def make_tool_name(*, catalog_name: str, operation: ApiOperation) -> str:
    """Create a suggested MCP tool name.

    Args:
        catalog_name: The API catalog name.
        operation: The normalized API operation.

    Returns:
        A suggested tool name.

    Raises:
        None.

    Examples:
        .. code-block:: python

            tool_name = make_tool_name(
                catalog_name="Petstore",
                operation=operation,
            )
    """
    return f"{make_catalog_slug(catalog_name)}__{make_operation_slug(operation)}"


def make_resource_uri(
    *,
    catalog_name: str,
    resource_kind: str,
    identifier: str,
) -> str:
    """Create a suggested MCP-style resource URI.

    Args:
        catalog_name: The API catalog name.
        resource_kind: The logical resource kind, such as ``operation`` or
            ``schema``.
        identifier: The resource identifier or slug.

    Returns:
        A suggested resource URI.

    Raises:
        None.

    Examples:
        .. code-block:: python

            uri = make_resource_uri(
                catalog_name="Petstore",
                resource_kind="operation",
                identifier="get-pet-by-id",
            )
    """
    return f"openapi://{make_catalog_slug(catalog_name)}/{slugify(resource_kind)}/{slugify(identifier)}"
