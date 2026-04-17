"""Manual test runner for the catalog surface planner agent."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from oas2mcp.agent.enhancer.agent import run_operation_enhancer
from oas2mcp.agent.runtime import Oas2McpRuntimeContext
from oas2mcp.agent.summarizer.agent import run_catalog_summarizer
from oas2mcp.agent.surface.agent import run_catalog_surface_planner
from oas2mcp.classify.operations import classify_catalog
from oas2mcp.generate.models import EnhancedCatalog
from oas2mcp.loaders.openapi import load_openapi_spec_dict
from oas2mcp.normalize.spec_to_catalog import spec_dict_to_catalog
from oas2mcp.utils.names import make_catalog_slug

SOURCE_URI = "https://petstore3.swagger.io/api/v3/openapi.json"


def main() -> None:
    """Run the catalog surface planner against a real enhanced catalog."""
    console = Console()

    spec_dict = load_openapi_spec_dict(SOURCE_URI)
    catalog = spec_dict_to_catalog(spec_dict, source_uri=SOURCE_URI)
    bundle = classify_catalog(catalog)

    runtime_context = Oas2McpRuntimeContext(
        source_uri=SOURCE_URI,
        output_style="compact",
        include_mcp_recommendations=True,
        include_risk_notes=True,
        project_name="oas2mcp",
        user_goal="Improve the shared FastMCP surface for this API.",
    )

    summary = run_catalog_summarizer(
        catalog=catalog,
        runtime_context=runtime_context,
    )
    operations = [
        run_operation_enhancer(
            catalog=catalog,
            bundle=bundle,
            summary=summary,
            operation=operation,
            runtime_context=runtime_context,
        )
        for operation in catalog.operations
    ]
    enhanced_catalog = EnhancedCatalog(
        source_url=SOURCE_URI,
        catalog_name=catalog.name,
        catalog_slug=make_catalog_slug(catalog.name),
        catalog_version=catalog.info.version,
        summary=summary,
        operations=operations,
        notes=["Manual surface-planner smoke test."],
    )

    surface_plan = run_catalog_surface_planner(
        enhanced_catalog=enhanced_catalog,
        runtime_context=runtime_context,
    )

    console.print(
        Panel(
            surface_plan.model_dump_json(indent=2),
            title="Catalog Surface Plan",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()
