"""Manual test runner for the catalog summarizer agent."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from oas2mcp.agent.runtime import Oas2McpRuntimeContext
from oas2mcp.agent.summarizer.agent import run_catalog_summarizer
from oas2mcp.loaders.openapi import load_openapi_spec_dict_from_url
from oas2mcp.normalize.spec_to_catalog import spec_dict_to_catalog

SOURCE_URI = "https://petstore3.swagger.io/api/v3/openapi.json"


def main() -> None:
    """Run the catalog summarizer agent end to end.

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

    runtime_context = Oas2McpRuntimeContext(
        source_uri=SOURCE_URI,
        output_style="compact",
        include_mcp_recommendations=True,
        include_risk_notes=True,
        project_name="oas2mcp",
        user_goal="Summarize this API for MCP planning.",
    )

    summary = run_catalog_summarizer(
        catalog=catalog,
        runtime_context=runtime_context,
    )

    console.print(
        Panel(
            summary.model_dump_json(indent=2),
            title="Catalog Summary",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()
