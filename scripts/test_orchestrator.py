"""Manual test runner for the end-to-end oas2mcp orchestrator."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from oas2mcp.agent.orchestrator import run_and_export_oas2mcp_pipeline
from oas2mcp.agent.runtime import Oas2McpRuntimeContext
from oas2mcp.generate.config import ExportConfig

SOURCE_URI = "https://petstore3.swagger.io/api/v3/openapi.json"


def main() -> None:
    """Run the summarize -> enhance-all -> export flow."""
    console = Console()

    runtime_context = Oas2McpRuntimeContext(
        source_uri=SOURCE_URI,
        output_style="compact",
        include_mcp_recommendations=True,
        include_risk_notes=False,
        project_name="oas2mcp",
        user_goal="Produce an enhanced API catalog for FastMCP export.",
    )

    export_config = ExportConfig(
        export_dir="data/exports",
        write_root_snapshot=False,
    )

    console.print(
        Panel(
            f"Starting orchestrator for:\n{SOURCE_URI}",
            title="oas2mcp Orchestrator",
            border_style="blue",
        )
    )
    console.print("Running summarize -> enhance-all -> export pipeline...")

    outputs = run_and_export_oas2mcp_pipeline(
        source_url=SOURCE_URI,
        runtime_context=runtime_context,
        export_config=export_config,
    )

    console.print()
    console.print(
        Panel(
            "\n".join([f"{name}: {path}" for name, path in outputs.items()]),
            title="Orchestrator Export",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()
