"""Manual test runner for MCP candidate classification.

Purpose:
    Load a public OpenAPI specification, normalize it into an
    :class:`~oas2mcp.models.normalized.ApiCatalog`, classify the resulting
    operations into first-pass MCP candidates, and render a Rich report.

Design:
    - Keep this as a lightweight development script.
    - Exercise the loader, normalizer, classifier, and classification viewer
      together.
    - Avoid depending on top-level package re-exports while the package API is
      still being stabilized.

Examples:
    .. code-block:: python

        pdm run python scripts/test_classification.py
"""

from __future__ import annotations

from rich.console import Console

from oas2mcp.classify.operations import classify_catalog
from oas2mcp.loaders.openapi import load_openapi_spec_dict_from_url
from oas2mcp.normalize.spec_to_catalog import spec_dict_to_catalog
from oas2mcp.viewers.classification import (
    render_mcp_bundle_summary,
    render_mcp_candidate_detail,
)

SOURCE_URI = "https://petstore3.swagger.io/api/v3/openapi.json"


def main() -> None:
    """Run the MCP candidate classification test flow.

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
    bundle = classify_catalog(catalog)

    render_mcp_bundle_summary(bundle, console=console, max_candidates=12)

    if bundle.candidates:
        console.print()
        render_mcp_candidate_detail(bundle.candidates[0], console=console)


if __name__ == "__main__":
    main()
