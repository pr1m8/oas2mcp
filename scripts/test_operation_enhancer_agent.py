"""Manual test runner for the operation enhancer agent.

Purpose:
    Load a public OpenAPI specification, normalize it into an
    :class:`~oas2mcp.models.normalized.ApiCatalog`, build the deterministic MCP
    candidate bundle, run the catalog summarizer, and then run the operation
    enhancer agent for one selected operation.

Design:
    - Keep this as a focused development script for one operation at a time.
    - Reuse the summarizer result as higher-level context for the enhancer.
    - Exercise loading, normalization, classification, summarization, enhancer
      context building, and the enhancer agent together.

Examples:
    .. code-block:: bash

        pdm run python scripts/test_operation_enhancer_agent.py
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from oas2mcp.agent.enhancer.agent import run_operation_enhancer
from oas2mcp.agent.runtime import Oas2McpRuntimeContext
from oas2mcp.agent.summarizer.agent import run_catalog_summarizer
from oas2mcp.classify.operations import classify_catalog
from oas2mcp.loaders.openapi import load_openapi_spec_dict_from_url
from oas2mcp.normalize.spec_to_catalog import spec_dict_to_catalog

SOURCE_URI = "https://petstore3.swagger.io/api/v3/openapi.json"
TARGET_OPERATION_KEY = "POST /pet"


def main() -> None:
    """Run the operation enhancer agent end to end.

    Args:
        None.

    Returns:
        None.

    Raises:
        RuntimeError: If the target operation cannot be found.

    Examples:
        .. code-block:: python

            main()
    """
    console = Console()

    spec_dict = load_openapi_spec_dict_from_url(SOURCE_URI)
    catalog = spec_dict_to_catalog(spec_dict, source_uri=SOURCE_URI)
    bundle = classify_catalog(catalog)

    runtime_context = Oas2McpRuntimeContext(
        source_uri=SOURCE_URI,
        output_style="compact",
        include_mcp_recommendations=True,
        include_risk_notes=False,
        project_name="oas2mcp",
        user_goal="Enhance one operation for later MCP/OpenAPI export.",
    )

    summary = run_catalog_summarizer(
        catalog=catalog,
        runtime_context=runtime_context,
    )

    target_operation = next(
        (
            operation
            for operation in catalog.operations
            if operation.key == TARGET_OPERATION_KEY
        ),
        None,
    )
    if target_operation is None:
        raise RuntimeError(
            f"Target operation {TARGET_OPERATION_KEY!r} was not found in the catalog."
        )

    enhancement = run_operation_enhancer(
        catalog=catalog,
        bundle=bundle,
        summary=summary,
        operation=target_operation,
        runtime_context=runtime_context,
    )

    console.print(
        Panel(
            "\n".join(
                [
                    f"Operation: {enhancement.operation_key}",
                    f"Slug: {enhancement.operation_slug}",
                    f"Final kind: {enhancement.final_kind}",
                    f"Title: {enhancement.title}",
                    f"Tool name: {enhancement.tool_name or '-'}",
                    f"Resource URI: {enhancement.resource_uri or '-'}",
                    f"Requires confirmation: {'yes' if enhancement.requires_confirmation else 'no'}",
                    f"Prompt templates: {len(enhancement.prompt_templates)}",
                ]
            ),
            title="Operation Enhancement Summary",
            border_style="green",
        )
    )
    console.print()
    console.print(
        Panel(
            enhancement.model_dump_json(indent=2),
            title="Operation Enhancement",
            border_style="yellow",
        )
    )


if __name__ == "__main__":
    main()
