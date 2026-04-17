"""LangGraph deployment entrypoints for ``oas2mcp``.

Purpose:
    Expose compiled LangGraph graphs that wrap the existing summarize/enhance
    pipeline so the project can be run with LangGraph CLI and deployed through
    LangSmith Deployments.

Design:
    - Keep the LangGraph layer thin and deterministic.
    - Reuse the existing orchestrator rather than reimplementing workflow logic.
    - Return JSON-serializable outputs suitable for LangGraph API responses.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

from oas2mcp.agent.orchestrator import (
    run_and_export_oas2mcp_pipeline,
    run_oas2mcp_pipeline,
)
from oas2mcp.agent.runtime import Oas2McpRuntimeContext
from oas2mcp.generate.config import ExportConfig


class Oas2McpGraphState(TypedDict):
    """State schema for LangGraph deployment wrappers."""

    source: str
    output_style: NotRequired[str]
    include_mcp_recommendations: NotRequired[bool]
    include_risk_notes: NotRequired[bool]
    project_name: NotRequired[str | None]
    user_goal: NotRequired[str | None]
    notes: NotRequired[list[str]]
    export_dir: NotRequired[str | None]
    write_root_snapshot: NotRequired[bool]
    root_snapshot_name: NotRequired[str | None]
    write_operation_notes: NotRequired[bool]
    write_fastmcp_config: NotRequired[bool]
    write_surface_plan: NotRequired[bool]
    result: NotRequired[dict[str, Any]]
    outputs: NotRequired[dict[str, str]]


def _build_runtime_context(state: Mapping[str, Any]) -> Oas2McpRuntimeContext:
    """Build runtime context from graph state."""
    return Oas2McpRuntimeContext(
        source_uri=str(state["source"]),
        output_style=str(state.get("output_style", "compact")),
        include_mcp_recommendations=bool(
            state.get("include_mcp_recommendations", True)
        ),
        include_risk_notes=bool(state.get("include_risk_notes", True)),
        project_name=state.get("project_name"),
        user_goal=state.get("user_goal"),
        notes=list(state.get("notes", [])),
    )


def _build_export_config(state: Mapping[str, Any]) -> ExportConfig:
    """Build export configuration from graph state."""
    config = ExportConfig(
        write_root_snapshot=bool(state.get("write_root_snapshot", False)),
        root_snapshot_name=state.get("root_snapshot_name"),
        write_operation_notes=bool(state.get("write_operation_notes", True)),
        write_fastmcp_config=bool(state.get("write_fastmcp_config", True)),
        write_surface_plan=bool(state.get("write_surface_plan", True)),
    )
    export_dir = state.get("export_dir")
    if export_dir:
        return config.model_copy(update={"export_dir": str(export_dir)})
    return config


def _run_pipeline_node(state: Oas2McpGraphState) -> dict[str, Any]:
    """Run the in-memory pipeline and return the enhanced catalog."""
    enhanced_catalog = run_oas2mcp_pipeline(
        source=state["source"],
        runtime_context=_build_runtime_context(state),
    )
    return {
        "result": enhanced_catalog.model_dump(mode="json"),
    }


def _run_export_pipeline_node(state: Oas2McpGraphState) -> dict[str, Any]:
    """Run the export pipeline and return artifact paths."""
    outputs = run_and_export_oas2mcp_pipeline(
        source=state["source"],
        runtime_context=_build_runtime_context(state),
        export_config=_build_export_config(state),
    )
    return {
        "outputs": {name: str(path) for name, path in outputs.items()},
    }


def _build_enhance_catalog_graph():
    """Build the graph that returns an enhanced catalog payload."""
    graph = StateGraph(Oas2McpGraphState)
    graph.add_node("run_pipeline", _run_pipeline_node)
    graph.add_edge(START, "run_pipeline")
    graph.add_edge("run_pipeline", END)
    return graph.compile()


def _build_enhance_and_export_catalog_graph():
    """Build the graph that writes export artifacts and returns their paths."""
    graph = StateGraph(Oas2McpGraphState)
    graph.add_node("run_export_pipeline", _run_export_pipeline_node)
    graph.add_edge(START, "run_export_pipeline")
    graph.add_edge("run_export_pipeline", END)
    return graph.compile()


enhance_catalog_graph = _build_enhance_catalog_graph()
enhance_and_export_catalog_graph = _build_enhance_and_export_catalog_graph()
