"""Run a bootstrapped FastMCP server for local inspection."""

from __future__ import annotations

from oas2mcp.generate.fastmcp_app import (
    build_fastmcp_from_exported_artifacts,
    register_exported_prompts,
)

SOURCE_URI = "https://petstore3.swagger.io/api/v3/openapi.json"
FASTMCP_CONFIG_PATH = "data/exports/swagger-petstore-openapi-3-0_fastmcp_config.json"


def main() -> None:
    """Build and run the FastMCP server locally."""
    mcp = build_fastmcp_from_exported_artifacts(
        source_url=SOURCE_URI,
        fastmcp_config_path=FASTMCP_CONFIG_PATH,
    )
    register_exported_prompts(mcp, FASTMCP_CONFIG_PATH)
    mcp.run(transport="http", port=8000)


if __name__ == "__main__":
    main()
