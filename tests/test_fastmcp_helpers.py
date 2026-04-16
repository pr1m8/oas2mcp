"""Tests for FastMCP export/bootstrap helper functions."""

from __future__ import annotations

from types import SimpleNamespace

from fastmcp.server.providers.openapi import MCPType

from oas2mcp.generate.fastmcp_app import (
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
                "resource_uri": "openapi://example-api/operation/inventory",
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
                "resource_uri": "openapi://example-api/operation/inventory",
            },
            "getstatus": {
                "operation_id": "getStatus",
                "resource_uri": "resource://status",
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
                    "final_kind": "resource",
                },
                "pet": {
                    "operation_id": "getPetById",
                    "final_kind": "tool",
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

    assert route_map_fn(inventory_route, default_type=MCPType.TOOL) == MCPType.RESOURCE
    assert (
        route_map_fn(order_route, default_type=MCPType.TOOL)
        == MCPType.RESOURCE_TEMPLATE
    )
    assert route_map_fn(pet_route, default_type=MCPType.RESOURCE) == MCPType.TOOL
