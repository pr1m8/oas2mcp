"""Typed state definitions for ``oas2mcp`` agents.

Purpose:
    Define the state carried through stateful OpenAPI enhancement workflows.

Design:
    - Use ``TypedDict`` because LangChain v1 custom agent state is typed this
      way.
    - Keep the state centered on the source URL and the progressively enriched
      understanding of the API.
    - Store deterministic catalog artifacts plus enhancer results so they can
      later be exported into a generated spec/config surface.

Examples:
    .. code-block:: python

        state: OpenApiEnhancementState = {
            "source_url": "https://example.com/openapi.json",
        }
"""

from __future__ import annotations

from typing import NotRequired, TypedDict

from langchain.agents import AgentState

from oas2mcp.agent.summarizer.context import CatalogSummaryContext
from oas2mcp.agent.summarizer.models import CatalogSummary
from oas2mcp.models.mcp import McpBundle
from oas2mcp.models.normalized import ApiCatalog


class OperationEnhancementRecord(TypedDict):
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

    catalog: NotRequired[ApiCatalog]
    candidate_bundle: NotRequired[McpBundle]
    catalog_summary_context: NotRequired[CatalogSummaryContext]
    catalog_summary: NotRequired[CatalogSummary]

    operation_keys: NotRequired[list[str]]
    current_operation_key: NotRequired[str]
    remaining_operation_keys: NotRequired[list[str]]

    enhancement_todo: NotRequired[list[str]]
    completed_steps: NotRequired[list[str]]

    enhanced_operations: NotRequired[list[OperationEnhancementRecord]]
    notes: NotRequired[list[str]]
