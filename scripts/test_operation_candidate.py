"""Manual test runner for single-operation MCP candidate inspection.

Purpose:
    Load a public OpenAPI specification, normalize it into an
    :class:`~oas2mcp.models.normalized.ApiCatalog`, locate one operation,
    classify it into a first-pass MCP candidate, and render both the raw
    operation and candidate detail views along with resolved schema refs.

Design:
    - Keep this as a focused development script for one operation at a time.
    - Support lookup by ``operationId`` or by ``METHOD + path``.
    - Exercise the loader, normalizer, lookup helpers, classifier, ref
      resolution, and Rich viewers together.
    - Avoid depending on top-level package re-exports while the package API is
      still being stabilized.

Examples:
    .. code-block:: bash

        pdm run python scripts/test_operation_candidate.py
        pdm run python scripts/test_operation_candidate.py --operation-id getPetById
        pdm run python scripts/test_operation_candidate.py --method POST --path /pet
"""

from __future__ import annotations

import argparse
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from oas2mcp.classify.operations import classify_operation
from oas2mcp.loaders.openapi import load_openapi_spec_dict_from_url
from oas2mcp.normalize.spec_to_catalog import spec_dict_to_catalog
from oas2mcp.utils.lookup import get_operation, get_operation_by_id
from oas2mcp.utils.refs import (
    collect_operation_schema_refs,
    dereference_schema_ref,
)
from oas2mcp.viewers.classification import (
    render_mcp_candidate_detail,
    render_operation_agent_context_preview,
)
from oas2mcp.viewers.summary import render_operation_detail

SOURCE_URI = "https://petstore3.swagger.io/api/v3/openapi.json"
DEFAULT_OPERATION_ID = "addPet"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the test runner.

    Args:
        None.

    Returns:
        argparse.Namespace: Parsed CLI arguments.

    Raises:
        None.

    Examples:
        .. code-block:: python

            args = parse_args()
    """
    parser = argparse.ArgumentParser(
        description="Inspect and classify a single OpenAPI operation."
    )
    parser.add_argument(
        "--operation-id",
        type=str,
        default=DEFAULT_OPERATION_ID,
        help="Operation ID to inspect. Ignored if both --method and --path are supplied.",
    )
    parser.add_argument(
        "--method",
        type=str,
        default=None,
        help="HTTP method for direct lookup, such as GET or POST.",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Operation path for direct lookup, such as /pet or /pet/{petId}.",
    )
    return parser.parse_args()


def build_schema_refs_table(
    *,
    schema_refs: list[str],
    resolved_schemas: dict[str, dict[str, Any] | None],
) -> Table:
    """Build a Rich table summarizing resolved schema refs.

    Args:
        schema_refs: Schema refs collected from the operation.
        resolved_schemas: Mapping of schema refs to resolved schema dictionaries.

    Returns:
        Table: A Rich table summarizing schema refs and their shapes.

    Raises:
        None.

    Examples:
        .. code-block:: python

            table = build_schema_refs_table(
                schema_refs=["#/components/schemas/Pet"],
                resolved_schemas={"#/components/schemas/Pet": {"type": "object"}},
            )
    """
    table = Table(title="Resolved Schema References")
    table.add_column("Schema Ref", style="cyan", overflow="fold")
    table.add_column("Resolved?", width=10)
    table.add_column("Type", width=14)
    table.add_column("Properties", justify="right", width=10)
    table.add_column("Keys", overflow="fold")

    if not schema_refs:
        table.add_row("-", "no", "-", "-", "No schema refs")
        return table

    for schema_ref in schema_refs:
        schema = resolved_schemas.get(schema_ref)
        if not isinstance(schema, dict):
            table.add_row(schema_ref, "no", "-", "-", "-")
            continue

        schema_type = schema.get("type")
        properties = schema.get("properties", {})
        property_count = len(properties) if isinstance(properties, dict) else 0
        key_preview = ", ".join(list(schema.keys())[:8]) or "-"

        table.add_row(
            schema_ref,
            "yes",
            str(schema_type or "-"),
            str(property_count),
            key_preview,
        )

    return table


def build_resolved_schema_panels(
    *,
    resolved_schemas: dict[str, dict[str, Any] | None],
) -> list[Panel]:
    """Build Rich panels for resolved schemas.

    Args:
        resolved_schemas: Mapping of schema refs to resolved schema dictionaries.

    Returns:
        list[Panel]: A list of Rich panels.

    Raises:
        None.

    Examples:
        .. code-block:: python

            panels = build_resolved_schema_panels(
                resolved_schemas={"#/components/schemas/Pet": {"type": "object"}},
            )
    """
    panels: list[Panel] = []

    for schema_ref, schema in resolved_schemas.items():
        if not isinstance(schema, dict):
            continue

        lines = []
        lines.append(f"type: {schema.get('type', '-')}")
        required = schema.get("required", [])
        if isinstance(required, list) and required:
            lines.append(f"required: {', '.join(str(item) for item in required)}")

        properties = schema.get("properties", {})
        if isinstance(properties, dict) and properties:
            property_names = ", ".join(list(properties.keys())[:12])
            lines.append(f"properties: {property_names}")

        all_of = schema.get("allOf")
        one_of = schema.get("oneOf")
        any_of = schema.get("anyOf")
        if isinstance(all_of, list):
            lines.append(f"allOf entries: {len(all_of)}")
        if isinstance(one_of, list):
            lines.append(f"oneOf entries: {len(one_of)}")
        if isinstance(any_of, list):
            lines.append(f"anyOf entries: {len(any_of)}")

        panels.append(
            Panel(
                "\n".join(lines) if lines else "(empty schema)",
                title=schema_ref,
                border_style="blue",
            )
        )

    return panels


def resolve_target_operation(
    *,
    operation_id: str | None,
    method: str | None,
    path: str | None,
    spec_url: str,
) -> tuple[Any, Any]:
    """Load the catalog and resolve the target operation.

    Args:
        operation_id: Operation ID to resolve.
        method: HTTP method to resolve.
        path: HTTP path to resolve.
        spec_url: Source OpenAPI URL.

    Returns:
        tuple[Any, Any]: The loaded catalog and resolved operation.

    Raises:
        SystemExit: If the operation cannot be found.

    Examples:
        .. code-block:: python

            catalog, operation = resolve_target_operation(
                operation_id="addPet",
                method=None,
                path=None,
                spec_url=SOURCE_URI,
            )
    """
    spec_dict = load_openapi_spec_dict_from_url(spec_url)
    catalog = spec_dict_to_catalog(spec_dict, source_uri=spec_url)

    if method and path:
        operation = get_operation(catalog, method=method, path=path)
    else:
        if not operation_id:
            raise SystemExit(
                "Either --operation-id or both --method and --path are required."
            )
        operation = get_operation_by_id(catalog, operation_id=operation_id)

    if operation is None:
        if method and path:
            raise SystemExit(f"Operation not found for {method.upper()} {path}.")
        raise SystemExit(f"Operation not found for operationId={operation_id!r}.")

    return catalog, operation


def main() -> None:
    """Run the single-operation inspection flow.

    Args:
        None.

    Returns:
        None.

    Raises:
        SystemExit: If the target operation cannot be found.

    Examples:
        .. code-block:: python

            main()
    """
    args = parse_args()
    console = Console()

    catalog, operation = resolve_target_operation(
        operation_id=args.operation_id,
        method=args.method,
        path=args.path,
        spec_url=SOURCE_URI,
    )
    candidate = classify_operation(catalog=catalog, operation=operation)

    schema_refs = collect_operation_schema_refs(operation)
    resolved_schemas = {
        schema_ref: dereference_schema_ref(catalog.raw_spec, schema_ref)
        for schema_ref in schema_refs
    }

    console.print(
        Panel(
            "\n".join(
                [
                    f"Catalog: {catalog.name}",
                    f"Source: {catalog.source_uri}",
                    f"Operation: {operation.key}",
                    f"operationId: {operation.operation_id or '-'}",
                    f"Schema refs: {len(schema_refs)}",
                ]
            ),
            title="Single Operation Test",
            border_style="green",
        )
    )
    console.print()
    render_operation_detail(operation, console=console)
    console.print()
    render_mcp_candidate_detail(candidate, console=console)
    console.print()
    render_operation_agent_context_preview(
        catalog=catalog,
        operation=operation,
        candidate=candidate,
        console=console,
    )
    console.print()
    console.print(
        build_schema_refs_table(
            schema_refs=schema_refs,
            resolved_schemas=resolved_schemas,
        )
    )

    panels = build_resolved_schema_panels(resolved_schemas=resolved_schemas)
    if panels:
        console.print()
        for panel in panels:
            console.print(panel)


if __name__ == "__main__":
    main()
