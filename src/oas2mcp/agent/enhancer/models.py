"""Typed state definitions for ``oas2mcp`` agents.

Purpose:
    Define the state carried through stateful OpenAPI enhancement workflows.

Design:
    - Use ``TypedDict`` because LangChain v1 custom agent state requires it.
    - Keep the state centered on the source URL and progressively enriched API
      understanding.
    - Store deterministic catalog artifacts plus enhancer results so they can
      later be exported into an enhanced spec/config surface.

Examples:
    .. code-block:: python

        state: OpenApiEnhancementState = {
            "source_url": "https://example.com/openapi.json",
        }
"""

from __future__ import annotations

from typing import NotRequired

from langchain.agents import AgentState


class OperationEnhancementRecord(AgentState):
    """Serializable enhancer result stored in agent state."""

    operation_key: str
    operation_slug: str
    final_kind: str
    title: str
    description: str
    requires_confirmation: bool
    tool_name: str | None
    resource_uri: str | None
    notes: list[str]


class OpenApiEnhancementState(AgentState):
    """State carried through the OpenAPI enhancement workflow."""

    source_url: str

    catalog: NotRequired[object]
    candidate_bundle: NotRequired[object]
    catalog_summary_context: NotRequired[object]
    catalog_summary: NotRequired[object]

    operation_keys: NotRequired[list[str]]
    current_operation_key: NotRequired[str]
    remaining_operation_keys: NotRequired[list[str]]

    enhancement_todo: NotRequired[list[str]]
    completed_steps: NotRequired[list[str]]

    enhanced_operations: NotRequired[list[OperationEnhancementRecord]]
    notes: NotRequired[list[str]]
