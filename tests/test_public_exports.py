"""Tests for public package export surfaces."""

from __future__ import annotations


def test_generate_package_exports_core_helpers() -> None:
    """The generate package should expose the documented public helpers."""
    from oas2mcp.generate import (
        CatalogPromptDefinition,
        CatalogResourceDefinition,
        EnhancedCatalog,
        ExportConfig,
        build_catalog_prompt_definitions,
        build_catalog_resource_definitions,
        build_fastmcp_config,
        build_fastmcp_from_exported_artifacts,
        build_fastmcp_from_loaded_artifacts,
        build_operation_notes_map,
        build_server_instructions,
        export_enhanced_catalog_bundle,
        register_exported_prompts,
        register_exported_resources,
    )

    assert CatalogPromptDefinition is not None
    assert CatalogResourceDefinition is not None
    assert ExportConfig is not None
    assert EnhancedCatalog is not None
    assert build_catalog_prompt_definitions is not None
    assert build_catalog_resource_definitions is not None
    assert build_fastmcp_config is not None
    assert build_operation_notes_map is not None
    assert build_server_instructions is not None
    assert export_enhanced_catalog_bundle is not None
    assert build_fastmcp_from_exported_artifacts is not None
    assert build_fastmcp_from_loaded_artifacts is not None
    assert register_exported_prompts is not None
    assert register_exported_resources is not None


def test_agent_subpackages_export_documented_entrypoints() -> None:
    """Summarizer and enhancer packages should expose their documented APIs."""
    from oas2mcp.agent.enhancer import (
        build_enhancer_agent,
        build_operation_enhancement_context,
        run_operation_enhancer,
    )
    from oas2mcp.agent.summarizer import (
        build_catalog_summarizer_agent,
        build_catalog_summary_context,
        run_catalog_summarizer,
    )
    from oas2mcp.agent.surface import (
        build_catalog_surface_planner_agent,
        build_catalog_surface_planning_context,
        run_catalog_surface_planner,
    )

    assert build_enhancer_agent is not None
    assert build_operation_enhancement_context is not None
    assert run_operation_enhancer is not None
    assert build_catalog_surface_planner_agent is not None
    assert build_catalog_surface_planning_context is not None
    assert run_catalog_surface_planner is not None
    assert build_catalog_summarizer_agent is not None
    assert build_catalog_summary_context is not None
    assert run_catalog_summarizer is not None
