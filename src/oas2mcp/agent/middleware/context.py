"""Middleware helpers for loading OpenAPI landscape context into agent state."""

from __future__ import annotations

from typing import Any

from oas2mcp.agent.runtime import Oas2McpRuntimeContext
from oas2mcp.agent.state import OpenApiEnhancementState
from oas2mcp.agent.summarizer.agent import run_catalog_summarizer
from oas2mcp.agent.summarizer.context import build_catalog_summary_context
from oas2mcp.classify.operations import classify_catalog
from oas2mcp.loaders.openapi import load_openapi_spec_dict_from_url
from oas2mcp.normalize.spec_to_catalog import spec_dict_to_catalog


def load_landscape_state(
    *,
    state: OpenApiEnhancementState,
    runtime_context: Oas2McpRuntimeContext,
    summarizer_model: Any | None = None,
) -> OpenApiEnhancementState:
    """Load normalized OpenAPI landscape artifacts into agent state."""
    if (
        "catalog" in state
        and "candidate_bundle" in state
        and "catalog_summary" in state
    ):
        return state

    source_url = state["source_url"]
    spec_dict = load_openapi_spec_dict_from_url(source_url)
    catalog = spec_dict_to_catalog(spec_dict, source_uri=source_url)
    bundle = classify_catalog(catalog)
    summary_context = build_catalog_summary_context(catalog, bundle=bundle)
    summary = run_catalog_summarizer(
        catalog=catalog,
        runtime_context=runtime_context,
        model=summarizer_model,
    )

    operation_keys = [operation.key for operation in catalog.operations]

    updated_state: OpenApiEnhancementState = {
        **state,
        "catalog": catalog,
        "candidate_bundle": bundle,
        "catalog_summary_context": summary_context,
        "catalog_summary": summary,
        "operation_keys": operation_keys,
        "remaining_operation_keys": operation_keys,
        "enhancement_todo": [
            f"Enhance {operation_key}" for operation_key in operation_keys
        ],
        "completed_steps": state.get("completed_steps", []),
        "enhanced_operations": state.get("enhanced_operations", []),
        "notes": state.get("notes", []),
    }
    return updated_state
