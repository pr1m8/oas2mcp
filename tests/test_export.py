"""Tests for enhanced catalog export helpers."""

from __future__ import annotations

from oas2mcp.agent.surface.models import (
    CatalogSurfacePlan,
    CatalogSurfacePromptPlan,
    CatalogSurfaceResourcePlan,
)
from oas2mcp.generate.export import (
    build_catalog_prompt_definitions,
    build_catalog_resource_definitions,
    build_fastmcp_config,
    build_fastmcp_name_map,
    build_server_instructions,
)


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
    assert config["catalog_version"] == "1.0.0"
    assert config["source_uri"] == "https://example.com/openapi.json"
    assert config["operations"]["getinventory"]["operation_id"] == "getInventory"
    assert config["operations"]["getorderbyid"]["final_kind"] == "resource_template"
    assert config["catalog_prompts"]
    assert config["catalog_resources"]
    assert config["surface_notes"] == []
    assert "getinventory" not in config["mcp_names"]


def test_default_catalog_surface_helpers_include_richer_prompts_and_resources(
    example_enhanced_catalog,
) -> None:
    """Deterministic defaults should expose shared planning helpers."""
    instructions = build_server_instructions(example_enhanced_catalog)
    prompts = build_catalog_prompt_definitions(example_enhanced_catalog)
    resources = build_catalog_resource_definitions(example_enhanced_catalog)

    assert "API purpose:" in instructions
    assert {prompt.name for prompt in prompts} == {
        "browse_namespace",
        "catalog_overview",
        "compare_operations",
        "plan_operation",
        "select_operation",
    }
    assert {resource.name for resource in resources} == {
        "catalog_summary",
        "namespace_operations",
        "operation_metadata",
        "prompt_index",
    }


def test_surface_plan_overrides_fastmcp_defaults(example_enhanced_catalog) -> None:
    """Export should prefer the planner output when a surface plan is present."""
    enhanced_catalog = example_enhanced_catalog.model_copy(
        update={
            "surface_plan": CatalogSurfacePlan(
                server_instructions="Custom server instructions.",
                catalog_prompts=[
                    CatalogSurfacePromptPlan(
                        name="custom_prompt",
                        title="Custom prompt",
                        description="A custom catalog prompt.",
                        template="Do the custom thing for {user_goal}.",
                        arguments=["user_goal"],
                    )
                ],
                catalog_resources=[
                    CatalogSurfaceResourcePlan(
                        kind="resource",
                        uri="oas2mcp://example-api/catalog/custom",
                        name="custom_resource",
                        title="Custom resource",
                        description="A custom catalog resource.",
                        payload={"status": "ok"},
                    )
                ],
                notes=["customized"],
            )
        }
    )

    config = build_fastmcp_config(enhanced_catalog)

    assert config["server_instructions"] == "Custom server instructions."
    assert [prompt["name"] for prompt in config["catalog_prompts"]] == ["custom_prompt"]
    assert [resource["name"] for resource in config["catalog_resources"]] == [
        "custom_resource"
    ]
    assert config["surface_notes"] == ["customized"]
