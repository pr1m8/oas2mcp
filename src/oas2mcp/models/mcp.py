"""MCP preparation models.

Purpose:
    Define structured intermediate models used to classify normalized OpenAPI
    operations into MCP-oriented candidates before any agent enhancement step.

Design:
    - Keep the first pass deterministic and lightweight.
    - Represent only the metadata needed before runtime/server generation.
    - Make these models suitable as structured output targets for later agents.

Examples:
    .. code-block:: python

        candidate = McpCandidate(
            operation_key="GET /pets/{petId}",
            kind="tool",
            title="Get pet by ID",
        )
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from oas2mcp.models.normalized import NormalizedBaseModel

McpCandidateKind = Literal[
    "tool",
    "resource",
    "resource_template",
    "prompt",
    "exclude",
]
McpSafetyLevel = Literal["safe_read", "mutating", "destructive"]


class McpPromptTemplate(NormalizedBaseModel):
    """A suggested prompt template derived from an API operation.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            prompt = McpPromptTemplate(
                name="explain-get-pet-by-id",
                title="Explain get pet by ID",
                description="Summarize how to use this endpoint.",
            )
    """

    name: str
    title: str
    description: str
    arguments: list[str] = Field(default_factory=list)
    template: str | None = None
    version: str | None = None
    tags: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class McpCandidate(NormalizedBaseModel):
    """A deterministic MCP candidate derived from one operation.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            candidate = McpCandidate(
                operation_key="GET /pets/{petId}",
                kind="tool",
                title="Get pet by ID",
                description="Retrieve a pet by its ID.",
            )
    """

    operation_key: str
    operation_slug: str
    kind: McpCandidateKind
    title: str
    description: str
    safety_level: McpSafetyLevel
    requires_confirmation: bool = False
    tool_name: str | None = None
    resource_uri: str | None = None
    auth_scheme_names: list[str] = Field(default_factory=list)
    auth_notes: str | None = None
    prompt_templates: list[McpPromptTemplate] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class McpBundle(NormalizedBaseModel):
    """A collection of MCP candidates for one catalog.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            bundle = McpBundle(
                catalog_name="Petstore",
                candidates=[],
            )
    """

    catalog_name: str
    catalog_slug: str
    candidates: list[McpCandidate] = Field(default_factory=list)
