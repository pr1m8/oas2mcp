"""Manual test runner for FastMCP bootstrap from exported oas2mcp artifacts."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from oas2mcp.generate.fastmcp_app import (
    build_fastmcp_from_exported_artifacts,
)

SOURCE_URI = "https://petstore3.swagger.io/api/v3/openapi.json"
FASTMCP_CONFIG_PATH = "data/exports/swagger-petstore-openapi-3-0_fastmcp_config.json"


def main() -> None:
    """Bootstrap a FastMCP server from exported artifacts."""
    console = Console()

    console.print(
        Panel(
            f"Bootstrapping FastMCP from:\n{SOURCE_URI}\n\nUsing config:\n{FASTMCP_CONFIG_PATH}",
            title="FastMCP Bootstrap",
            border_style="blue",
        )
    )

    mcp = build_fastmcp_from_exported_artifacts(
        source_url=SOURCE_URI,
        fastmcp_config_path=FASTMCP_CONFIG_PATH,
    )

    console.print(
        Panel(
            "\n".join(
                [
                    f"Server object: {type(mcp).__name__}",
                    "Bootstrap succeeded.",
                    "Next step: run the server and inspect tools/resources via a client.",
                ]
            ),
            title="FastMCP Bootstrap Result",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()
