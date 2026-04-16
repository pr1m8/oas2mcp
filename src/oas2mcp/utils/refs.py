"""Reference and JSON pointer helpers.

Purpose:
    Resolve JSON pointers and schema references against normalized OpenAPI raw
    spec data.

Design:
    - Support local ``#/...`` references first.
    - Keep helpers read-only and deterministic.
    - Return ``None`` instead of raising for missing refs in normal lookup
      flows.
    - Provide separate request and response schema ref collection so viewers
      and agent-context builders can distinguish input from output structure.

Examples:
    .. code-block:: python

        schema = dereference_schema_ref(catalog.raw_spec, "#/components/schemas/Pet")
"""

from __future__ import annotations

from typing import Any

from oas2mcp.models.normalized import ApiOperation


def resolve_json_pointer(document: dict[str, Any], pointer: str) -> Any | None:
    """Resolve a local JSON pointer within a document.

    Args:
        document: The target document.
        pointer: The JSON pointer, such as ``#/components/schemas/Pet``.

    Returns:
        The resolved value when found, otherwise ``None``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            value = resolve_json_pointer(
                {"components": {"schemas": {"Pet": {"type": "object"}}}},
                "#/components/schemas/Pet",
            )
    """
    if not pointer.startswith("#/"):
        return None

    current: Any = document
    parts = pointer[2:].split("/")

    for raw_part in parts:
        part = raw_part.replace("~1", "/").replace("~0", "~")

        if isinstance(current, dict) and part in current:
            current = current[part]
            continue

        if isinstance(current, list):
            try:
                index = int(part)
            except ValueError:
                return None
            if index < 0 or index >= len(current):
                return None
            current = current[index]
            continue

        return None

    return current


def dereference_schema_ref(
    document: dict[str, Any],
    schema_ref: str,
) -> dict[str, Any] | None:
    """Dereference a local schema reference.

    Args:
        document: The raw OpenAPI specification dictionary.
        schema_ref: A local schema reference.

    Returns:
        The resolved schema mapping when found, otherwise ``None``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            schema = dereference_schema_ref(
                {"components": {"schemas": {"Pet": {"type": "object"}}}},
                "#/components/schemas/Pet",
            )
    """
    value = resolve_json_pointer(document, schema_ref)
    if isinstance(value, dict):
        return value
    return None


def collect_request_schema_refs(operation: ApiOperation) -> list[str]:
    """Collect request-body schema refs mentioned by an operation.

    Args:
        operation: The normalized API operation.

    Returns:
        A de-duplicated list of request schema refs.

    Raises:
        None.

    Examples:
        .. code-block:: python

            refs = collect_request_schema_refs(operation)
    """
    collected: list[str] = []

    if operation.request_body is not None:
        for media_type in operation.request_body.media_types:
            if media_type.schema_ref:
                collected.append(media_type.schema_ref)

    return _deduplicate_refs(collected)


def collect_response_schema_refs(operation: ApiOperation) -> list[str]:
    """Collect response schema refs mentioned by an operation.

    Args:
        operation: The normalized API operation.

    Returns:
        A de-duplicated list of response schema refs.

    Raises:
        None.

    Examples:
        .. code-block:: python

            refs = collect_response_schema_refs(operation)
    """
    collected: list[str] = []

    for response in operation.responses:
        for media_type in response.media_types:
            if media_type.schema_ref:
                collected.append(media_type.schema_ref)

    return _deduplicate_refs(collected)


def collect_operation_schema_refs(operation: ApiOperation) -> list[str]:
    """Collect all schema refs mentioned by an operation.

    Args:
        operation: The normalized API operation.

    Returns:
        A de-duplicated list of request and response schema refs.

    Raises:
        None.

    Examples:
        .. code-block:: python

            refs = collect_operation_schema_refs(operation)
    """
    return _deduplicate_refs(
        [
            *collect_request_schema_refs(operation),
            *collect_response_schema_refs(operation),
        ]
    )


def _deduplicate_refs(schema_refs: list[str]) -> list[str]:
    """Deduplicate schema refs while preserving order.

    Args:
        schema_refs: The candidate schema refs.

    Returns:
        A de-duplicated list of refs.

    Raises:
        None.

    Examples:
        .. code-block:: python

            refs = _deduplicate_refs(["#/A", "#/A", "#/B"])
            assert refs == ["#/A", "#/B"]
    """
    seen: set[str] = set()
    ordered: list[str] = []

    for item in schema_refs:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)

    return ordered
