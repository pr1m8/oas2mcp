"""Deterministic context builders for the operation enhancer agent.

Purpose:
    Build compact, structured context objects for refining one normalized API
    operation into a more MCP-friendly representation.

Design:
    - Keep context building deterministic and side-effect free.
    - Combine normalized operation data, deterministic MCP candidate data,
      resolved schemas, and catalog summary context.
    - Treat deterministic MCP candidate values as hints rather than final
      truth.
    - Keep the enhancer context focused on the current operation.

Examples:
    .. code-block:: python

        context = build_operation_enhancement_context(
            catalog=catalog,
            bundle=bundle,
            summary=summary,
            operation=operation,
        )
"""

from __future__ import annotations

from oas2mcp.agent.enhancer.models import (
    EnhancementPromptCandidate,
    OperationEnhancementContext,
    ResolvedSchemaContext,
    SecuritySchemeContext,
)
from oas2mcp.agent.summarizer.models import CatalogSummary
from oas2mcp.models.mcp import McpBundle, McpCandidate
from oas2mcp.models.normalized import ApiCatalog, ApiOperation
from oas2mcp.utils.lookup import get_security_scheme
from oas2mcp.utils.names import make_catalog_slug
from oas2mcp.utils.refs import (
    collect_request_schema_refs,
    collect_response_schema_refs,
    dereference_schema_ref,
)


def build_operation_enhancement_context(
    *,
    catalog: ApiCatalog,
    bundle: McpBundle,
    summary: CatalogSummary,
    operation: ApiOperation,
) -> OperationEnhancementContext:
    """Build deterministic enhancer context for one operation.

    Args:
        catalog: The normalized API catalog.
        bundle: The deterministic MCP bundle.
        summary: The catalog-level summary.
        operation: The operation to enhance.

    Returns:
        OperationEnhancementContext: Deterministic context for one operation.

    Raises:
        KeyError: If no MCP candidate exists for the operation.

    Examples:
        .. code-block:: python

            context = build_operation_enhancement_context(
                catalog=catalog,
                bundle=bundle,
                summary=summary,
                operation=operation,
            )
    """
    candidate = _get_candidate(bundle, operation.key)
    request_refs = collect_request_schema_refs(operation)
    response_refs = collect_response_schema_refs(operation)

    merged_refs: list[str] = []
    for schema_ref in [*request_refs, *response_refs]:
        if schema_ref not in merged_refs:
            merged_refs.append(schema_ref)

    resolved_schemas = []
    for schema_ref in merged_refs:
        schema_object = dereference_schema_ref(catalog.raw_spec, schema_ref)
        if schema_object is not None:
            resolved_schemas.append(
                ResolvedSchemaContext(
                    schema_ref=schema_ref,
                    schema_object=schema_object,
                )
            )

    security_schemes = []
    for scheme_name in candidate.auth_scheme_names:
        scheme = get_security_scheme(catalog, name=scheme_name)
        if scheme is None:
            continue
        security_schemes.append(
            SecuritySchemeContext(
                name=scheme.name,
                type=scheme.type,
                location=scheme.location,
                parameter_name=scheme.parameter_name,
                scheme=scheme.scheme,
                bearer_format=scheme.bearer_format,
                flow_names=sorted(list(scheme.flows.keys())),
            )
        )

    return OperationEnhancementContext(
        catalog_name=catalog.name,
        catalog_slug=make_catalog_slug(catalog.name),
        source_uri=catalog.source_uri,
        server_urls=[server.url for server in catalog.servers],
        catalog_summary_purpose=summary.api_purpose,
        catalog_domains=[domain.tag_name for domain in summary.primary_domains],
        operation_key=operation.key,
        operation_id=operation.operation_id,
        operation_slug=candidate.operation_slug,
        method=operation.method,
        path=operation.path,
        summary=operation.summary,
        description=operation.description,
        tags=list(operation.tags),
        candidate_kind_hint=candidate.kind,
        candidate_tool_name_hint=candidate.tool_name,
        candidate_resource_uri_hint=candidate.resource_uri,
        candidate_requires_confirmation_hint=candidate.requires_confirmation,
        candidate_prompt_templates=[
            EnhancementPromptCandidate.model_validate(
                prompt.model_dump(),
            )
            for prompt in candidate.prompt_templates
        ],
        request_schema_refs=request_refs,
        response_schema_refs=response_refs,
        resolved_schemas=resolved_schemas,
        path_parameter_names=[
            parameter.name
            for parameter in operation.parameters
            if parameter.location == "path"
        ],
        query_parameter_names=[
            parameter.name
            for parameter in operation.parameters
            if parameter.location == "query"
        ],
        security_schemes=security_schemes,
    )


def _get_candidate(bundle: McpBundle, operation_key: str) -> McpCandidate:
    """Return the candidate associated with an operation key.

    Args:
        bundle: The MCP bundle.
        operation_key: The target operation key.

    Returns:
        McpCandidate: The matching candidate.

    Raises:
        KeyError: If no candidate is found.

    Examples:
        .. code-block:: python

            candidate = _get_candidate(bundle, "POST /pet")
    """
    for candidate in bundle.candidates:
        if candidate.operation_key == operation_key:
            return candidate
    raise KeyError(f"No MCP candidate found for operation key {operation_key!r}.")
