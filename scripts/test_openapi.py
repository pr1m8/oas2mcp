"""Manual test runner for ``oas2mcp``.

Purpose:
    Load a public OpenAPI spec, normalize it into an ``ApiCatalog``, and
    render Rich output for local development.

Design:
    - Keep this as a simple development script.
    - Exercise the loader, normalizer, and viewer together.

Examples:
    .. code-block:: python

        pdm run python scripts/test_openapi.py
"""

from __future__ import annotations

from rich.console import Console

from oas2mcp.loaders.openapi import load_openapi_spec_dict_from_url
from oas2mcp.normalize.spec_to_catalog import spec_dict_to_catalog
from oas2mcp.viewers.summary import (
    render_catalog_summary,
    render_operation_detail,
)

SOURCE_URI = "https://petstore3.swagger.io/api/v3/openapi.json"


def main() -> None:
    """Run the local OpenAPI test flow.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            main()
    """
    console = Console()
    spec_dict = load_openapi_spec_dict_from_url(SOURCE_URI)
    catalog = spec_dict_to_catalog(spec_dict, source_uri=SOURCE_URI)

    render_catalog_summary(catalog, console=console)

    if catalog.operations:
        console.print()
        render_operation_detail(catalog.operations[0], console=console)


if __name__ == "__main__":
    main()
