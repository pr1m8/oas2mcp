"""Inspect a locally running FastMCP server with the FastMCP client."""

from __future__ import annotations

import asyncio

from fastmcp import Client


async def main() -> None:
    """Connect to the local FastMCP server and print counts and names."""
    async with Client("http://127.0.0.1:8000/mcp") as client:
        await client.ping()

        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()

        print(f"Tools: {len(tools)}")
        for tool in tools[:20]:
            print(f"  - {tool.name}")

        print(f"\nResources: {len(resources)}")
        for resource in resources[:20]:
            print(f"  - {resource.name}")

        print(f"\nPrompts: {len(prompts)}")
        for prompt in prompts[:20]:
            print(f"  - {prompt.name}")


if __name__ == "__main__":
    asyncio.run(main())
