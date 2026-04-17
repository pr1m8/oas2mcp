"""Tests for FastMCP export/bootstrap helper functions."""

from __future__ import annotations

from types import SimpleNamespace

from fastmcp.server.providers.openapi import MCPType

from oas2mcp.generate.fastmcp_app import (
    build_export_aware_component_fn,
    build_export_aware_route_map_fn,
    build_fastmcp_name_overrides,
)


def test_build_fastmcp_name_overrides_prefers_explicit_mapping() -> None:
    """Explicit exported name overrides should win when present."""
    config = {
        "mcp_names": {
            "getInventory": "inventory",
            "createPet": "create_pet",
        },
        "operations": {
            "ignored": {
                "operation_id": "getInventory",
                "resource_uri": "openapi://example-api/inventory",
            }
        },
    }

    assert build_fastmcp_name_overrides(config) == {
        "getInventory": "inventory",
        "createPet": "create_pet",
    }


def test_build_fastmcp_name_overrides_derives_names_from_operation_metadata() -> None:
    """Generated names should fall back to tool names or resource URIs."""
    config = {
        "operations": {
            "getinventory": {
                "operation_id": "getInventory",
                "resource_uri": "openapi://example-api/inventory",
            },
            "getstatus": {
                "operation_id": "getStatus",
                "resource_uri": "openapi://example-api/status",
            },
            "createpet": {
                "operation_id": "createPet",
                "tool_name": "create_pet",
            },
        }
    }

    assert build_fastmcp_name_overrides(config) == {
        "getInventory": "inventory",
        "getStatus": "status",
        "createPet": "create_pet",
    }


def test_build_export_aware_route_map_fn_respects_final_kind_and_path_params() -> None:
    """Exported final kinds should override semantic defaults consistently."""
    route_map_fn = build_export_aware_route_map_fn(
        {
            "operations": {
                "inventory": {
                    "operation_id": "getInventory",
                    "final_kind": "resource",
                },
                "order": {
                    "operation_id": "getOrderById",
                    "final_kind": "resource_template",
                },
                "pet": {
                    "operation_id": "getPetById",
                    "final_kind": "tool",
                },
                "deprecated": {
                    "operation_id": "deletePet",
                    "final_kind": "exclude",
                },
            }
        }
    )

    inventory_route = SimpleNamespace(
        operation_id="getInventory",
        parameters=[],
    )
    order_route = SimpleNamespace(
        operation_id="getOrderById",
        parameters=[SimpleNamespace(location="path")],
    )
    pet_route = SimpleNamespace(
        operation_id="getPetById",
        parameters=[SimpleNamespace(location="path")],
    )
    excluded_route = SimpleNamespace(
        operation_id="deletePet",
        parameters=[],
    )

    assert route_map_fn(inventory_route, default_type=MCPType.TOOL) == MCPType.RESOURCE
    assert (
        route_map_fn(order_route, default_type=MCPType.TOOL)
        == MCPType.RESOURCE_TEMPLATE
    )
    assert route_map_fn(pet_route, default_type=MCPType.RESOURCE) == MCPType.TOOL
    assert route_map_fn(excluded_route, default_type=MCPType.TOOL) == MCPType.EXCLUDE


def test_build_export_aware_component_fn_applies_exported_metadata() -> None:
    """Exported metadata should mutate generated FastMCP components."""
    component_fn = build_export_aware_component_fn(
        {
            "operations": {
                "getorderbyid": {
                    "operation_id": "getOrderById",
                    "final_kind": "resource_template",
                    "title": "Order details",
                    "description": "Inspect one order.",
                    "resource_uri": "openapi://example-api/orders/{orderId}",
                    "component_version": "1.0.0",
                    "component_tags": ["store", "read"],
                    "component_meta": {"generated_by": "oas2mcp"},
                    "component_annotations": {"audience": ["assistant"]},
                }
            }
        }
    )

    route = SimpleNamespace(
        operation_id="getOrderById",
        parameters=[
            SimpleNamespace(
                name="orderId",
                location="path",
                required=True,
                schema={"type": "string"},
            ),
            SimpleNamespace(
                name="include",
                location="query",
                required=False,
                schema={"type": "string"},
            ),
        ],
    )
    component = SimpleNamespace(
        title=None,
        description=None,
        version=None,
        tags=set(),
        meta={},
        annotations=None,
        uri_template="resource://placeholder/{orderId}",
        parameters={},
    )

    updated = component_fn(route, component)

    assert updated.title == "Order details"
    assert updated.description == "Inspect one order."
    assert updated.version == "1.0.0"
    assert updated.tags == {"store", "read"}
    assert updated.meta["generated_by"] == "oas2mcp"
    assert updated.uri_template == "openapi://example-api/orders/{orderId}"
    assert updated.parameters["properties"]["include"]["type"] == "string"
