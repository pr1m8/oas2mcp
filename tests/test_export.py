"""Tests for enhanced catalog export helpers."""

from __future__ import annotations

from oas2mcp.generate.export import build_fastmcp_config, build_fastmcp_name_map


def test_build_fastmcp_name_map_keys_by_operation_id(example_enhanced_catalog) -> None:
    """FastMCP name overrides must be keyed by OpenAPI operationId."""
    name_map = build_fastmcp_name_map(example_enhanced_catalog)

    assert set(name_map) == {
        "getInventory",
        "getOrderById",
        "getPetById",
        "createPet",
    }
    assert name_map["getInventory"] == "inventory"
    assert name_map["getOrderById"] == "order_details"
    assert name_map["getPetById"] == "pet_by_id"


def test_build_fastmcp_config_includes_operation_metadata(
    example_enhanced_catalog,
) -> None:
    """Exported config should retain operation identifiers for bootstrap decisions."""
    config = build_fastmcp_config(example_enhanced_catalog)

    assert config["catalog_slug"] == "example-api"
    assert config["operations"]["getinventory"]["operation_id"] == "getInventory"
    assert config["operations"]["getorderbyid"]["final_kind"] == "resource"
    assert "getinventory" not in config["mcp_names"]
