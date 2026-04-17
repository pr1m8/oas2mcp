"""Catalog surface planner exports for ``oas2mcp``.

Purpose:
    Provide a small public surface for the catalog-level FastMCP planning
    workflow without eagerly importing the full agent stack during package
    initialization.
"""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "CatalogSurfaceOperationContext",
    "CatalogSurfacePlan",
    "CatalogSurfacePlanningContext",
    "CatalogSurfacePromptPlan",
    "CatalogSurfaceResourcePlan",
    "DEFAULT_SURFACE_MODEL_NAME",
    "DEFAULT_SURFACE_REASONING_EFFORT",
    "build_catalog_surface_planner_agent",
    "build_catalog_surface_planning_context",
    "run_catalog_surface_planner",
]


def __getattr__(name: str):
    """Resolve public exports lazily to avoid import cycles."""
    if name in {
        "CatalogSurfaceOperationContext",
        "CatalogSurfacePlan",
        "CatalogSurfacePlanningContext",
        "CatalogSurfacePromptPlan",
        "CatalogSurfaceResourcePlan",
    }:
        module = import_module("oas2mcp.agent.surface.models")
        return getattr(module, name)

    if name == "build_catalog_surface_planning_context":
        module = import_module("oas2mcp.agent.surface.context")
        return getattr(module, name)

    if name in {
        "DEFAULT_SURFACE_MODEL_NAME",
        "DEFAULT_SURFACE_REASONING_EFFORT",
        "build_catalog_surface_planner_agent",
        "run_catalog_surface_planner",
    }:
        module = import_module("oas2mcp.agent.surface.agent")
        return getattr(module, name)

    raise AttributeError(name)
