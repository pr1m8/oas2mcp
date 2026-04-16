"""Inspect a locally running FastMCP server.

Run ``scripts/test_fastmcp_server.py`` first, then use this script to confirm
the exported surface and a simple resource read over HTTP.
"""

from __future__ import annotations

import asyncio

from fastmcp import Client


async def main() -> None:
    """Connect to the local FastMCP server and print its exported surface."""
    async with Client("http://127.0.0.1:8000/mcp") as client:
        await client.ping()

        tools = await client.list_tools()
        resources = await client.list_resources()
        templates = await client.list_resource_templates()
        prompts = await client.list_prompts()

        print(f"Tools: {len(tools)}")
        for tool in tools[:20]:
            print(f"  - {tool.name}")

        print(f"\nResources: {len(resources)}")
        for resource in resources[:20]:
            print(f"  - {resource.name}")

        print(f"\nResource templates: {len(templates)}")
        for template in templates[:20]:
            print(f"  - {template.name}")

        print(f"\nPrompts: {len(prompts)}")
        for prompt in prompts[:20]:
            print(f"  - {prompt.name}")

        inventory_resource = next(
            (
                resource
                for resource in resources
                if getattr(resource, "name", None) == "inventory"
            ),
            None,
        )
        if inventory_resource is not None:
            content = await client.read_resource(inventory_resource.uri)
            print("\nInventory resource result:")
            print(content)


if __name__ == "__main__":
    asyncio.run(main())
