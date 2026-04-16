"""Enhancer-supporting tools for the operation enhancement workflow."""

from __future__ import annotations

from langchain.tools import tool

from oas2mcp.agent.state import OpenApiEnhancementState


@tool
def list_remaining_operation_keys(state: OpenApiEnhancementState) -> list[str]:
    """List operation keys that still need enhancement.

    Args:
        state: The current agent state.

    Returns:
        A list of remaining operation keys.
    """
    return list(state.get("remaining_operation_keys", []))


@tool
def get_current_operation_key(state: OpenApiEnhancementState) -> str | None:
    """Return the current operation key being enhanced.

    Args:
        state: The current agent state.

    Returns:
        The current operation key, if present.
    """
    return state.get("current_operation_key")
