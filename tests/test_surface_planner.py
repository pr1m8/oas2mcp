"""Tests for the catalog surface planner agent layer."""

from __future__ import annotations

from oas2mcp.agent.runtime import Oas2McpRuntimeContext
from oas2mcp.agent.surface.agent import (
    _apply_catalog_surface_plan_defaults,
    run_catalog_surface_planner,
)
from oas2mcp.agent.surface.context import build_catalog_surface_planning_context
from oas2mcp.agent.surface.models import (
    CatalogSurfacePlan,
    CatalogSurfacePromptPlan,
    CatalogSurfaceResourcePlan,
)


def test_build_catalog_surface_planning_context_includes_default_surface_hints(
    example_enhanced_catalog,
) -> None:
    """The planner context should include deterministic prompt/resource defaults."""
    context = build_catalog_surface_planning_context(example_enhanced_catalog)

    assert context.default_server_instructions
    assert {prompt.name for prompt in context.default_catalog_prompts} == {
        "browse_namespace",
        "catalog_overview",
        "compare_operations",
        "plan_operation",
        "select_operation",
    }
    assert {resource.name for resource in context.default_catalog_resources} == {
        "catalog_summary",
        "namespace_operations",
        "operation_metadata",
        "prompt_index",
    }


def test_apply_catalog_surface_plan_defaults_merges_with_defaults(
    example_enhanced_catalog,
) -> None:
    """Planner output should preserve defaults while allowing curated additions."""
    context = build_catalog_surface_planning_context(example_enhanced_catalog)
    plan = CatalogSurfacePlan(
        server_instructions="Use the custom shared surface.",
        catalog_prompts=[
            CatalogSurfacePromptPlan(
                name="custom_goal_router",
                title="Custom goal router",
                description="Route a user goal to the right namespace.",
                template="Find the best namespace for {user_goal}.",
                arguments=["user_goal"],
            )
        ],
        catalog_resources=[
            CatalogSurfaceResourcePlan(
                kind="resource",
                uri="oas2mcp://example-api/catalog/custom",
                name="custom_catalog_resource",
                title="Custom catalog resource",
                description="Custom resource payload.",
                payload={"kind": "custom"},
            )
        ],
    )

    normalized = _apply_catalog_surface_plan_defaults(plan, context=context)

    assert normalized.server_instructions == "Use the custom shared surface."
    assert {prompt.name for prompt in normalized.catalog_prompts} >= {
        "catalog_overview",
        "custom_goal_router",
    }
    assert {resource.name for resource in normalized.catalog_resources} >= {
        "catalog_summary",
        "custom_catalog_resource",
        "namespace_operations",
    }

    custom_prompt = next(
        prompt
        for prompt in normalized.catalog_prompts
        if prompt.name == "custom_goal_router"
    )
    assert custom_prompt.meta["catalog_slug"] == "example-api"


def test_run_catalog_surface_planner_normalizes_agent_output(
    monkeypatch,
    example_enhanced_catalog,
) -> None:
    """The planner runner should normalize sparse model output."""

    class _FakeAgent:
        def invoke(self, *_args, **_kwargs):
            return {
                "structured_response": CatalogSurfacePlan(
                    server_instructions="",
                    catalog_prompts=[
                        CatalogSurfacePromptPlan(
                            name="catalog_overview",
                            title="",
                            description="",
                            template="",
                        )
                    ],
                    catalog_resources=[],
                )
            }

    monkeypatch.setattr(
        "oas2mcp.agent.surface.agent.build_catalog_surface_planner_agent",
        lambda **_kwargs: _FakeAgent(),
    )

    runtime_context = Oas2McpRuntimeContext(
        source_uri="https://example.com/openapi.json",
        project_name="oas2mcp",
        user_goal="Improve the shared FastMCP surface.",
    )

    plan = run_catalog_surface_planner(
        enhanced_catalog=example_enhanced_catalog,
        runtime_context=runtime_context,
    )

    assert "API purpose:" in plan.server_instructions
    assert {prompt.name for prompt in plan.catalog_prompts} >= {"catalog_overview"}
    assert {resource.name for resource in plan.catalog_resources} >= {
        "catalog_summary",
        "namespace_operations",
    }
