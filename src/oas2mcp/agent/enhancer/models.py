"""Structured models for the operation enhancer agent.

Purpose:
    Define deterministic input and structured output models for refining one
    normalized API operation into a more MCP-friendly representation.

Design:
    - Keep these models specific to the enhancer workflow.
    - Separate deterministic context objects from LLM-produced enhancement
      outputs.
    - Treat deterministic MCP classification data as hints rather than final
      truth.
    - Preserve enough detail for naming, auth, confirmation, and later export.

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

from typing import Any

from pydantic import Field

from oas2mcp.models.mcp import McpCandidateKind
from oas2mcp.models.normalized import NormalizedBaseModel


class ResolvedSchemaContext(NormalizedBaseModel):
    """Resolved schema context for one schema reference.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            schema_context = ResolvedSchemaContext(
                schema_ref="#/components/schemas/Pet",
                schema_object={"type": "object"},
            )
    """

    schema_ref: str
    schema_object: dict = Field(default_factory=dict)


class SecuritySchemeContext(NormalizedBaseModel):
    """Compact security scheme details used by the enhancer.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            scheme = SecuritySchemeContext(
                name="petstore_auth",
                type="oauth2",
                flow_names=["implicit"],
            )
    """

    name: str
    type: str
    location: str | None = None
    parameter_name: str | None = None
    scheme: str | None = None
    bearer_format: str | None = None
    flow_names: list[str] = Field(default_factory=list)


class EnhancementPromptCandidate(NormalizedBaseModel):
    """Suggested prompt template for an enhanced operation.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            prompt = EnhancementPromptCandidate(
                name="create-pet",
                title="Create pet",
                description="Create a new pet safely.",
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


class OperationEnhancementContext(NormalizedBaseModel):
    """Deterministic agent-facing context for one operation.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            context = OperationEnhancementContext(
                catalog_name="Petstore",
                catalog_slug="petstore",
                source_uri="https://example.com/openapi.json",
                catalog_summary_purpose="Manage pets and orders.",
                catalog_domains=["pet", "store", "user"],
                operation_key="POST /pet",
                operation_slug="addpet",
                method="POST",
                path="/pet",
                candidate_kind_hint="tool",
            )
    """

    catalog_name: str
    catalog_slug: str
    source_uri: str
    server_urls: list[str] = Field(default_factory=list)

    catalog_summary_purpose: str
    catalog_domains: list[str] = Field(default_factory=list)

    operation_key: str
    operation_id: str | None = None
    operation_slug: str
    method: str
    path: str
    summary: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)

    candidate_kind_hint: str
    candidate_tool_name_hint: str | None = None
    candidate_resource_uri_hint: str | None = None
    candidate_requires_confirmation_hint: bool = False
    candidate_prompt_templates: list[EnhancementPromptCandidate] = Field(
        default_factory=list
    )

    request_schema_refs: list[str] = Field(default_factory=list)
    response_schema_refs: list[str] = Field(default_factory=list)
    resolved_schemas: list[ResolvedSchemaContext] = Field(default_factory=list)
    path_parameter_names: list[str] = Field(default_factory=list)
    query_parameter_names: list[str] = Field(default_factory=list)

    security_schemes: list[SecuritySchemeContext] = Field(default_factory=list)


class OperationEnhancement(NormalizedBaseModel):
    """Structured enhancement result for one operation.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            enhancement = OperationEnhancement(
                operation_key="POST /pet",
                operation_slug="addpet",
                final_kind="tool",
                title="Create pet",
                description="Create a new pet record.",
            )
    """

    operation_key: str
    operation_id: str | None = None
    operation_slug: str

    final_kind: McpCandidateKind
    namespace: str | None = None
    title: str
    description: str

    component_name: str | None = None
    tool_name: str | None = None
    resource_uri: str | None = None
    component_version: str | None = None
    component_tags: list[str] = Field(default_factory=list)
    component_meta: dict[str, Any] = Field(default_factory=dict)
    component_annotations: dict[str, Any] = Field(default_factory=dict)

    requires_confirmation: bool = False
    auth_notes: str | None = None

    prompt_templates: list[EnhancementPromptCandidate] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
