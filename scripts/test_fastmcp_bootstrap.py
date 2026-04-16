"""Manual test runner for FastMCP bootstrap from exported oas2mcp artifacts."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from oas2mcp.generate.fastmcp_app import (
    build_fastmcp_from_exported_artifacts,
    register_exported_prompts,
)

SOURCE_URI = "https://petstore3.swagger.io/api/v3/openapi.json"
FASTMCP_CONFIG_PATH = "data/exports/swagger-petstore-openapi-3-0_fastmcp_config.json"


def main() -> None:
    """Bootstrap a FastMCP server from exported artifacts."""
    console = Console()

    mcp = build_fastmcp_from_exported_artifacts(
        source_url=SOURCE_URI,
        fastmcp_config_path=FASTMCP_CONFIG_PATH,
    )
    register_exported_prompts(mcp, FASTMCP_CONFIG_PATH)

    console.print(
        Panel(
            "FastMCP bootstrap succeeded with semantic route maps and exported prompts.",
            title="FastMCP Bootstrap Result",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()
