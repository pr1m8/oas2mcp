"""Enhancer-supporting tools for the operation enhancement workflow."""

from __future__ import annotations

from langchain.tools import ToolRuntime, tool

from oas2mcp.agent.runtime import Oas2McpRuntimeContext
from oas2mcp.agent.state import OpenApiEnhancementState


@tool
def list_remaining_operation_keys(
    runtime: ToolRuntime[Oas2McpRuntimeContext, OpenApiEnhancementState],
) -> list[str]:
    """List operation keys that still need enhancement."""
    return list(runtime.state.get("remaining_operation_keys", []))


@tool
def get_current_operation_key(
    runtime: ToolRuntime[Oas2McpRuntimeContext, OpenApiEnhancementState],
) -> str | None:
    """Return the current operation key being enhanced."""
    return runtime.state.get("current_operation_key")
