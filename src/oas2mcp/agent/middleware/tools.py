"""Enhancer-supporting tools for ``oas2mcp`` agents."""

from __future__ import annotations

from typing import Any

from langchain.tools import tool

from oas2mcp.agent.state import OpenApiEnhancementState


@tool
def list_remaining_operation_keys(state: OpenApiEnhancementState) -> list[str]:
    """List the remaining operation keys that still need enhancement."""
    return list(state.get("remaining_operation_keys", []))


@tool
def list_completed_steps(state: OpenApiEnhancementState) -> list[str]:
    """List completed enhancer workflow steps."""
    return list(state.get("completed_steps", []))
