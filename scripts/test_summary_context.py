"""Manual test runner for catalog summarizer context building.

Purpose:
    Load a public OpenAPI specification, normalize it into an
    :class:`~oas2mcp.models.normalized.ApiCatalog`, classify it into a first
    MCP bundle, and build the deterministic context for the first catalog-level
    summarizer agent.

Design:
    - Keep this as a lightweight development script.
    - Exercise loading, normalization, deterministic classification, and
      summarizer-context building together.
    - Print JSON so the next summarizer prompt/runner stage has a concrete
      target payload.

Examples:
    .. code-block:: bash

        pdm run python scripts/test_catalog_summary_context.py
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from oas2mcp.agent.summarizer.context import build_catalog_summary_context
from oas2mcp.classify.operations import classify_catalog
from oas2mcp.loaders.openapi import load_openapi_spec_dict_from_url
from oas2mcp.normalize.spec_to_catalog import spec_dict_to_catalog

SOURCE_URI = "https://petstore3.swagger.io/api/v3/openapi.json"


def main() -> None:
    """Run the catalog summarizer context test flow.

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
    context = build_catalog_summary_context(catalog, bundle=bundle)

    console.print(
        Panel(
            "\n".join(
                [
                    f"Catalog: {context.catalog_name}",
                    f"Slug: {context.catalog_slug}",
                    f"Operations: {context.operation_count}",
                    f"Candidates: {context.candidate_count}",
                    f"Tags: {len(context.tag_summaries)}",
                    f"Security schemes: {', '.join(context.security_scheme_names) or '-'}",
                ]
            ),
            title="Catalog Summary Context",
            border_style="green",
        )
    )
    console.print()
    console.print(context.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
