"""Lookup helpers for normalized catalogs.

Purpose:
    Provide convenient query helpers over normalized ``ApiCatalog`` objects so
    later classifiers and agents can work with targeted slices of the spec.

Design:
    - Keep helpers deterministic and side-effect free.
    - Return ``None`` for missing singular lookups rather than raising.
    - Preserve original operation objects rather than copying them.

Examples:
    .. code-block:: python

        operation = get_operation(catalog, method="GET", path="/pets/{petId}")
        tagged = list_operations_by_tag(catalog, tag="pet")
"""

from __future__ import annotations

from oas2mcp.models.normalized import (
    ApiCatalog,
    ApiOperation,
    ApiSecurityScheme,
)


def get_operation(
    catalog: ApiCatalog,
    *,
    method: str,
    path: str,
) -> ApiOperation | None:
    """Return one operation by HTTP method and path.

    Args:
        catalog: The normalized API catalog.
        method: The HTTP method to match.
        path: The normalized or raw operation path.

    Returns:
        The matching operation if found, otherwise ``None``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            operation = get_operation(
                catalog,
                method="GET",
                path="/pets/{petId}",
            )
    """
    normalized_method = method.upper()
    normalized_path = path if path.startswith("/") else f"/{path}"

    for operation in catalog.operations:
        if operation.method == normalized_method and operation.path == normalized_path:
            return operation
    return None


def get_operation_by_id(
    catalog: ApiCatalog,
    *,
    operation_id: str,
) -> ApiOperation | None:
    """Return one operation by ``operationId``.

    Args:
        catalog: The normalized API catalog.
        operation_id: The target ``operationId``.

    Returns:
        The matching operation if found, otherwise ``None``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            operation = get_operation_by_id(
                catalog,
                operation_id="getPetById",
            )
    """
    for operation in catalog.operations:
        if operation.operation_id == operation_id:
            return operation
    return None


def list_operations_by_tag(
    catalog: ApiCatalog,
    *,
    tag: str,
) -> list[ApiOperation]:
    """Return all operations associated with a tag.

    Args:
        catalog: The normalized API catalog.
        tag: The tag name to match.

    Returns:
        A list of matching operations.

    Raises:
        None.

    Examples:
        .. code-block:: python

            pet_operations = list_operations_by_tag(catalog, tag="pet")
    """
    return [operation for operation in catalog.operations if tag in operation.tags]


def list_mutating_operations(catalog: ApiCatalog) -> list[ApiOperation]:
    """Return all mutating operations.

    Args:
        catalog: The normalized API catalog.

    Returns:
        A list of mutating operations.

    Raises:
        None.

    Examples:
        .. code-block:: python

            mutating = list_mutating_operations(catalog)
    """
    return [operation for operation in catalog.operations if operation.is_mutating]


def list_read_operations(catalog: ApiCatalog) -> list[ApiOperation]:
    """Return all non-mutating operations.

    Args:
        catalog: The normalized API catalog.

    Returns:
        A list of read-oriented operations.

    Raises:
        None.

    Examples:
        .. code-block:: python

            reads = list_read_operations(catalog)
    """
    return [operation for operation in catalog.operations if not operation.is_mutating]


def get_security_scheme(
    catalog: ApiCatalog,
    *,
    name: str,
) -> ApiSecurityScheme | None:
    """Return one security scheme by name.

    Args:
        catalog: The normalized API catalog.
        name: The security scheme name.

    Returns:
        The matching security scheme if found, otherwise ``None``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            scheme = get_security_scheme(catalog, name="api_key")
    """
    for scheme in catalog.security_schemes:
        if scheme.name == name:
            return scheme
    return None
