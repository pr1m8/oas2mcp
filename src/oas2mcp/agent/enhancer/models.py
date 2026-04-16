"""Structured models for the operation enhancer agent.

Purpose:
    Define deterministic input and structured output models for refining one
    normalized API operation into a more MCP-friendly representation.

Design:
    - Keep these models specific to the enhancer workflow.
    - Separate deterministic context objects from LLM-produced enhancement
      outputs.
    - Preserve enough detail for naming, auth, confirmation, and export.

Examples:
    .. code-block:: python

        enhancement = OperationEnhancement(
            operation_key="POST /pet",
            operation_slug="addpet",
            final_kind="tool",
            title="Create pet",
            description="Create a new pet record.",
            requires_confirmation=False,
        )
"""

from __future__ import annotations

from pydantic import Field

from oas2mcp.models.normalized import NormalizedBaseModel


class ResolvedSchemaContext(NormalizedBaseModel):
    """Resolved schema context for one schema reference."""

    schema_ref: str
    schema: dict = Field(default_factory=dict)


class SecuritySchemeContext(NormalizedBaseModel):
    """Compact security scheme details used by the enhancer."""

    name: str
    type: str
    location: str | None = None
    parameter_name: str | None = None
    scheme: str | None = None
    bearer_format: str | None = None
    flow_names: list[str] = Field(default_factory=list)


class EnhancementPromptCandidate(NormalizedBaseModel):
    """Suggested prompt template for an enhanced operation."""

    name: str
    title: str
    description: str
    arguments: list[str] = Field(default_factory=list)


class OperationEnhancement(NormalizedBaseModel):
    """Structured enhancement result for one operation."""

    operation_key: str
    operation_slug: str

    final_kind: str
    namespace: str | None = None
    title: str
    description: str

    tool_name: str | None = None
    resource_uri: str | None = None

    requires_confirmation: bool = False
    auth_notes: str | None = None

    prompt_templates: list[EnhancementPromptCandidate] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
