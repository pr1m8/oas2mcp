"""Tests for the summarize-enhance-export orchestrator pipeline."""

from __future__ import annotations

import json

from oas2mcp.agent.orchestrator import (
    run_and_export_oas2mcp_pipeline,
    run_oas2mcp_pipeline,
)
from oas2mcp.agent.runtime import Oas2McpRuntimeContext
from oas2mcp.agent.surface.models import CatalogSurfacePlan
from oas2mcp.generate.config import ExportConfig


def test_run_oas2mcp_pipeline_builds_enhanced_catalog(
    monkeypatch,
    example_openapi_spec,
    example_summary,
    example_enhanced_catalog,
) -> None:
    """The orchestrator should stitch together load, summarize, and enhance steps."""
    recorded_operation_ids: list[str | None] = []

    monkeypatch.setattr(
        "oas2mcp.agent.orchestrator.load_openapi_spec_dict",
        lambda source: example_openapi_spec,
    )
    monkeypatch.setattr(
        "oas2mcp.agent.orchestrator.run_catalog_summarizer",
        lambda **kwargs: example_summary,
    )
    monkeypatch.setattr(
        "oas2mcp.agent.orchestrator.run_catalog_surface_planner",
        lambda **kwargs: CatalogSurfacePlan(
            server_instructions="Use the exported MCP surface.",
            notes=["planner-ran"],
        ),
    )

    enhancement_by_id = {
        operation.operation_id: operation
        for operation in example_enhanced_catalog.operations
    }

    def fake_enhancer(**kwargs):
        operation = kwargs["operation"]
        recorded_operation_ids.append(operation.operation_id)
        return enhancement_by_id[operation.operation_id]

    monkeypatch.setattr(
        "oas2mcp.agent.orchestrator.run_operation_enhancer",
        fake_enhancer,
    )

    runtime_context = Oas2McpRuntimeContext(
        source_uri="https://example.com/openapi.json",
        project_name="oas2mcp",
        user_goal="Run the pipeline",
    )

    enhanced_catalog = run_oas2mcp_pipeline(
        source="https://example.com/openapi.json",
        runtime_context=runtime_context,
    )

    assert enhanced_catalog.catalog_name == "Example API"
    assert enhanced_catalog.catalog_slug == "example-api"
    assert enhanced_catalog.catalog_version == "1.0.0"
    assert enhanced_catalog.summary == example_summary
    assert enhanced_catalog.surface_plan is not None
    assert enhanced_catalog.surface_plan.notes == ["planner-ran"]
    assert recorded_operation_ids == [
        "getInventory",
        "getOrderById",
        "getPetById",
        "createPet",
    ]
    assert [operation.operation_id for operation in enhanced_catalog.operations] == [
        "getInventory",
        "getOrderById",
        "getPetById",
        "createPet",
    ]


def test_run_and_export_oas2mcp_pipeline_writes_expected_artifacts(
    monkeypatch,
    tmp_path,
    example_openapi_spec,
    example_summary,
    example_enhanced_catalog,
) -> None:
    """The export wrapper should write enhanced catalog artifacts to disk."""
    monkeypatch.setattr(
        "oas2mcp.agent.orchestrator.load_openapi_spec_dict",
        lambda source: example_openapi_spec,
    )
    monkeypatch.setattr(
        "oas2mcp.agent.orchestrator.run_catalog_summarizer",
        lambda **kwargs: example_summary,
    )
    monkeypatch.setattr(
        "oas2mcp.agent.orchestrator.run_catalog_surface_planner",
        lambda **kwargs: CatalogSurfacePlan(
            server_instructions="Use the exported MCP surface.",
            notes=["planner-ran"],
        ),
    )

    enhancement_by_id = {
        operation.operation_id: operation
        for operation in example_enhanced_catalog.operations
    }
    monkeypatch.setattr(
        "oas2mcp.agent.orchestrator.run_operation_enhancer",
        lambda **kwargs: enhancement_by_id[kwargs["operation"].operation_id],
    )

    runtime_context = Oas2McpRuntimeContext(
        source_uri="https://example.com/openapi.json",
        project_name="oas2mcp",
        user_goal="Run and export the pipeline",
    )
    export_config = ExportConfig(
        project_root=tmp_path,
        export_dir="exports",
        write_root_snapshot=False,
    )

    outputs = run_and_export_oas2mcp_pipeline(
        source="https://example.com/openapi.json",
        runtime_context=runtime_context,
        export_config=export_config,
    )

    assert set(outputs) == {
        "enhanced_catalog",
        "operation_notes",
        "surface_plan",
        "fastmcp_config",
    }
    for path in outputs.values():
        assert path.exists()

    fastmcp_config = json.loads(outputs["fastmcp_config"].read_text(encoding="utf-8"))
    assert fastmcp_config["catalog_name"] == "Example API"
    assert fastmcp_config["mcp_names"]["getInventory"] == "inventory"
    assert fastmcp_config["surface_notes"] == ["planner-ran"]
