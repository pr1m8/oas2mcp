"""End-to-end tests for the FastMCP bootstrap path."""

from __future__ import annotations

import asyncio
import json

from fastmcp import Client

from oas2mcp.generate.export import build_fastmcp_config
from oas2mcp.generate.fastmcp_app import (
    build_fastmcp_from_exported_artifacts,
    register_exported_prompts,
    register_exported_resources,
)


def test_fastmcp_bootstrap_supports_tool_resource_template_and_prompt_invocation(
    tmp_path,
    monkeypatch,
    example_openapi_spec,
    example_enhanced_catalog,
    upstream_client,
) -> None:
    """The exported FastMCP surface should be invokable end to end in-process."""
    config = build_fastmcp_config(example_enhanced_catalog)
    config_path = tmp_path / "fastmcp_config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    monkeypatch.setattr(
        "oas2mcp.generate.fastmcp_app.fetch_openapi_spec",
        lambda source, timeout=30.0: example_openapi_spec,
    )

    mcp = build_fastmcp_from_exported_artifacts(
        source="https://example.com/openapi.json",
        fastmcp_config_path=config_path,
        client=upstream_client,
    )
    register_exported_resources(mcp, config_path)
    register_exported_prompts(mcp, config_path)

    async def run() -> None:
        async with Client(mcp) as client:
            tool_names = {tool.name for tool in await client.list_tools()}
            resource_names = {
                resource.name for resource in await client.list_resources()
            }
            template_names = {
                template.name for template in await client.list_resource_templates()
            }
            prompt_names = {prompt.name for prompt in await client.list_prompts()}

            assert tool_names == {"create_pet", "pet_by_id"}
            assert resource_names == {
                "catalog_summary",
                "inventory",
                "prompt_index",
            }
            assert template_names == {
                "namespace_operations",
                "operation_metadata",
                "order_details",
            }
            assert prompt_names == {
                "browse_namespace",
                "catalog_overview",
                "compare_operations",
                "plan_operation",
                "select_operation",
                "draft_pet_creation",
                "lookup_order",
                "view_inventory",
            }

            summary = await client.read_resource(
                "oas2mcp://example-api/catalog/summary"
            )
            assert '"catalog_slug": "example-api"' in _resource_text(summary)

            prompt_index = await client.read_resource(
                "oas2mcp://example-api/catalog/prompts"
            )
            assert '"catalog_prompts"' in _resource_text(prompt_index)

            inventory = await client.read_resource("openapi://example-api/inventory")
            assert '"available": 3' in _resource_text(inventory)

            order = await client.read_resource("openapi://example-api/orders/42")
            assert '"id": "42"' in _resource_text(order)

            operation_metadata = await client.read_resource(
                "oas2mcp://example-api/operations/getorderbyid"
            )
            assert '"operation_id": "getOrderById"' in _resource_text(
                operation_metadata
            )

            namespace_operations = await client.read_resource(
                "oas2mcp://example-api/namespaces/store/operations"
            )
            assert '"namespace": "store"' in _resource_text(namespace_operations)

            pet = await client.call_tool("pet_by_id", {"petId": "7"})
            assert pet.structured_content["id"] == "7"

            created_pet = await client.call_tool("create_pet", {"name": "Nova"})
            assert created_pet.structured_content["name"] == "Nova"

            prompt = await client.get_prompt("lookup_order", {"orderId": "42"})
            assert "42" in _prompt_text(prompt)

    asyncio.run(run())


def _resource_text(contents: list[object]) -> str:
    """Return a combined text payload from resource contents."""
    return "\n".join(
        content.text
        for content in contents
        if hasattr(content, "text") and isinstance(content.text, str)
    )


def _prompt_text(prompt_result: object) -> str:
    """Return a combined text payload from a prompt result."""
    messages = getattr(prompt_result, "messages", [])
    parts: list[str] = []
    for message in messages:
        content = getattr(message, "content", None)
        text = getattr(content, "text", None)
        if isinstance(text, str):
            parts.append(text)
    return "\n".join(parts)
