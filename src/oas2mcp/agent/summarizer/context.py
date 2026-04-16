"""Deterministic context builders for the catalog summarizer agent.

Purpose:
    Build compact, structured context objects for the catalog-level summarizer
    agent using normalized catalogs and optional MCP candidate bundles.

Design:
    - Keep context building deterministic and side-effect free.
    - Emphasize the API's purpose, conceptual structure, domains, data model,
      and request/response patterns.
    - Preserve lightweight operational and MCP-oriented signals without letting
      them dominate the summarizer's input.
    - Support summarization with or without a classified MCP bundle.

Examples:
    .. code-block:: python

        context = build_catalog_summary_context(catalog, bundle=bundle)
        print(context.catalog_name)
        print(context.primary_schema_refs[0].schema_ref)
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from pydantic import Field

from oas2mcp.models.mcp import McpBundle, McpCandidate
from oas2mcp.models.normalized import (
    ApiCatalog,
    ApiOperation,
    ApiSecurityScheme,
    NormalizedBaseModel,
)
from oas2mcp.utils.lookup import (
    list_mutating_operations,
    list_operations_by_tag,
    list_read_operations,
)
from oas2mcp.utils.names import make_catalog_slug
from oas2mcp.utils.refs import (
    collect_request_schema_refs,
    collect_response_schema_refs,
)


class CatalogSecuritySchemeContext(NormalizedBaseModel):
    """Compact security scheme context for summarizer input.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            scheme = CatalogSecuritySchemeContext(
                name="api_key",
                type="apiKey",
                location="header",
                parameter_name="X-API-Key",
            )
    """

    name: str
    type: str
    location: str | None = None
    parameter_name: str | None = None
    scheme: str | None = None
    bearer_format: str | None = None
    flow_names: list[str] = Field(default_factory=list)


class SchemaRefSummary(NormalizedBaseModel):
    """Compact rollup for frequently referenced schema refs.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            summary = SchemaRefSummary(
                schema_ref="#/components/schemas/Pet",
                count=4,
            )
    """

    schema_ref: str
    count: int


class CandidateExample(NormalizedBaseModel):
    """Compact MCP candidate example for summarizer input.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            candidate = CandidateExample(
                operation_key="GET /pets/{id}",
                operation_slug="get-pet-by-id",
                kind="resource",
                title="Get pet by ID",
                safety_level="safe_read",
            )
    """

    operation_key: str
    operation_slug: str
    kind: str
    title: str
    safety_level: str
    tool_name: str | None = None
    resource_uri: str | None = None


class CatalogTagContext(NormalizedBaseModel):
    """Deterministic tag/domain context for summarizer input.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            tag_context = CatalogTagContext(
                tag_name="pet",
                description="Everything about your Pets",
                operation_count=8,
            )
    """

    tag_name: str
    description: str
    operation_count: int = 0
    read_operation_count: int = 0
    mutating_operation_count: int = 0
    operation_ids: list[str] = Field(default_factory=list)
    operation_keys: list[str] = Field(default_factory=list)
    notable_operations: list[str] = Field(default_factory=list)


class CatalogSummaryContext(NormalizedBaseModel):
    """Compact agent-facing context for catalog-level summarization.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            context = CatalogSummaryContext(
                catalog_name="Petstore",
                catalog_slug="petstore",
                source_uri="https://example.com/openapi.json",
            )
    """

    catalog_name: str
    catalog_slug: str
    source_uri: str
    openapi_version: str | None = None

    info_title: str | None = None
    info_version: str | None = None
    info_summary: str | None = None
    info_description: str | None = None

    server_urls: list[str] = Field(default_factory=list)

    tag_summaries: list[CatalogTagContext] = Field(default_factory=list)

    operation_count: int = 0
    read_operation_count: int = 0
    mutating_operation_count: int = 0
    destructive_operation_count: int = 0
    deprecated_operation_count: int = 0

    component_counts: dict[str, int] = Field(default_factory=dict)

    security_schemes: list[CatalogSecuritySchemeContext] = Field(default_factory=list)

    primary_schema_refs: list[SchemaRefSummary] = Field(default_factory=list)
    request_schema_refs: list[SchemaRefSummary] = Field(default_factory=list)
    response_schema_refs: list[SchemaRefSummary] = Field(default_factory=list)

    candidate_count: int = 0
    candidate_kind_counts: dict[str, int] = Field(default_factory=dict)
    candidate_safety_counts: dict[str, int] = Field(default_factory=dict)

    sample_tool_candidates: list[CandidateExample] = Field(default_factory=list)
    sample_resource_candidates: list[CandidateExample] = Field(default_factory=list)

    notable_operations: list[str] = Field(default_factory=list)
    notable_read_operations: list[str] = Field(default_factory=list)
    notable_mutating_operations: list[str] = Field(default_factory=list)


def build_catalog_summary_context(
    catalog: ApiCatalog,
    bundle: McpBundle | None = None,
) -> CatalogSummaryContext:
    """Build deterministic summarizer context for an API catalog.

    Args:
        catalog: The normalized API catalog.
        bundle: Optional MCP bundle produced by deterministic classification.

    Returns:
        A compact ``CatalogSummaryContext`` suitable for a summarizer agent.

    Raises:
        None.

    Examples:
        .. code-block:: python

            context = build_catalog_summary_context(catalog, bundle=bundle)
    """
    read_operations = list_read_operations(catalog)
    mutating_operations = list_mutating_operations(catalog)
    destructive_operations = [
        operation for operation in catalog.operations if operation.method == "DELETE"
    ]
    deprecated_operations = [
        operation for operation in catalog.operations if operation.deprecated
    ]

    candidate_kind_counts: dict[str, int] = {}
    candidate_safety_counts: dict[str, int] = {}
    candidate_count = 0
    sample_tool_candidates: list[CandidateExample] = []
    sample_resource_candidates: list[CandidateExample] = []

    if bundle is not None:
        candidate_count = len(bundle.candidates)
        candidate_kind_counts = dict(
            Counter(candidate.kind for candidate in bundle.candidates)
        )
        candidate_safety_counts = dict(
            Counter(candidate.safety_level for candidate in bundle.candidates)
        )
        sample_tool_candidates = _build_candidate_examples(
            [candidate for candidate in bundle.candidates if candidate.kind == "tool"],
            limit=3,
        )
        sample_resource_candidates = _build_candidate_examples(
            [
                candidate
                for candidate in bundle.candidates
                if candidate.kind == "resource"
            ],
            limit=3,
        )

    tag_summaries = _build_tag_contexts(catalog)
    security_schemes = _build_security_scheme_contexts(catalog.security_schemes)
    request_schema_refs = _build_top_schema_ref_summaries(
        catalog.operations,
        request=True,
        limit=6,
    )
    response_schema_refs = _build_top_schema_ref_summaries(
        catalog.operations,
        request=False,
        limit=6,
    )
    primary_schema_refs = _merge_schema_ref_summaries(
        request_schema_refs,
        response_schema_refs,
        limit=8,
    )

    return CatalogSummaryContext(
        catalog_name=catalog.name,
        catalog_slug=make_catalog_slug(catalog.name),
        source_uri=catalog.source_uri,
        openapi_version=catalog.openapi_version,
        info_title=catalog.info.title if catalog.info is not None else None,
        info_version=catalog.info.version if catalog.info is not None else None,
        info_summary=catalog.info.summary if catalog.info is not None else None,
        info_description=catalog.info.description if catalog.info is not None else None,
        server_urls=[server.url for server in catalog.servers],
        tag_summaries=tag_summaries,
        operation_count=catalog.operation_count,
        read_operation_count=len(read_operations),
        mutating_operation_count=len(mutating_operations),
        destructive_operation_count=len(destructive_operations),
        deprecated_operation_count=len(deprecated_operations),
        component_counts=dict(catalog.component_counts),
        security_schemes=security_schemes,
        primary_schema_refs=primary_schema_refs,
        request_schema_refs=request_schema_refs,
        response_schema_refs=response_schema_refs,
        candidate_count=candidate_count,
        candidate_kind_counts=candidate_kind_counts,
        candidate_safety_counts=candidate_safety_counts,
        sample_tool_candidates=sample_tool_candidates,
        sample_resource_candidates=sample_resource_candidates,
        notable_operations=_collect_notable_operation_keys(catalog.operations),
        notable_read_operations=_collect_notable_operation_keys(read_operations),
        notable_mutating_operations=_collect_notable_operation_keys(
            mutating_operations
        ),
    )


def _build_tag_contexts(catalog: ApiCatalog) -> list[CatalogTagContext]:
    """Build deterministic tag/domain contexts from a catalog.

    Args:
        catalog: The normalized API catalog.

    Returns:
        A list of ``CatalogTagContext`` entries.

    Raises:
        None.

    Examples:
        .. code-block:: python

            tag_contexts = _build_tag_contexts(catalog)
    """
    tag_contexts: list[CatalogTagContext] = []

    for tag in catalog.tags:
        tagged_operations = list_operations_by_tag(catalog, tag=tag.name)
        read_count = len(
            [operation for operation in tagged_operations if not operation.is_mutating]
        )
        mutating_count = len(
            [operation for operation in tagged_operations if operation.is_mutating]
        )

        tag_contexts.append(
            CatalogTagContext(
                tag_name=tag.name,
                description=tag.description or "",
                operation_count=len(tagged_operations),
                read_operation_count=read_count,
                mutating_operation_count=mutating_count,
                operation_ids=[
                    operation.operation_id
                    for operation in tagged_operations
                    if operation.operation_id is not None
                ],
                operation_keys=[operation.key for operation in tagged_operations],
                notable_operations=_collect_notable_operation_keys(
                    tagged_operations,
                    limit=5,
                ),
            )
        )

    untagged_operations = [
        operation for operation in catalog.operations if not operation.tags
    ]
    if untagged_operations:
        tag_contexts.append(
            CatalogTagContext(
                tag_name="untagged",
                description="Operations without explicit tags.",
                operation_count=len(untagged_operations),
                read_operation_count=len(
                    [
                        operation
                        for operation in untagged_operations
                        if not operation.is_mutating
                    ]
                ),
                mutating_operation_count=len(
                    [
                        operation
                        for operation in untagged_operations
                        if operation.is_mutating
                    ]
                ),
                operation_ids=[
                    operation.operation_id
                    for operation in untagged_operations
                    if operation.operation_id is not None
                ],
                operation_keys=[operation.key for operation in untagged_operations],
                notable_operations=_collect_notable_operation_keys(
                    untagged_operations,
                    limit=5,
                ),
            )
        )

    return tag_contexts


def _build_security_scheme_contexts(
    schemes: list[ApiSecurityScheme],
) -> list[CatalogSecuritySchemeContext]:
    """Build compact security scheme context entries.

    Args:
        schemes: The normalized security schemes.

    Returns:
        A list of compact security scheme contexts.

    Raises:
        None.

    Examples:
        .. code-block:: python

            contexts = _build_security_scheme_contexts(catalog.security_schemes)
    """
    return [
        CatalogSecuritySchemeContext(
            name=scheme.name,
            type=scheme.type,
            location=scheme.location,
            parameter_name=scheme.parameter_name,
            scheme=scheme.scheme,
            bearer_format=scheme.bearer_format,
            flow_names=sorted(list(scheme.flows.keys())),
        )
        for scheme in schemes
    ]


def _build_top_schema_ref_summaries(
    operations: Iterable[ApiOperation],
    *,
    request: bool,
    limit: int,
) -> list[SchemaRefSummary]:
    """Build compact top schema-ref summaries.

    Args:
        operations: The candidate operations.
        request: Whether to collect request refs or response refs.
        limit: Maximum number of entries to return.

    Returns:
        A list of schema-ref summaries.

    Raises:
        None.

    Examples:
        .. code-block:: python

            summaries = _build_top_schema_ref_summaries(
                catalog.operations,
                request=True,
                limit=5,
            )
    """
    counter: Counter[str] = Counter()

    for operation in operations:
        refs = (
            collect_request_schema_refs(operation)
            if request
            else collect_response_schema_refs(operation)
        )
        counter.update(refs)

    return [
        SchemaRefSummary(schema_ref=schema_ref, count=count)
        for schema_ref, count in counter.most_common(limit)
    ]


def _merge_schema_ref_summaries(
    request_summaries: list[SchemaRefSummary],
    response_summaries: list[SchemaRefSummary],
    *,
    limit: int,
) -> list[SchemaRefSummary]:
    """Merge request and response schema-ref summaries.

    Args:
        request_summaries: Request schema summaries.
        response_summaries: Response schema summaries.
        limit: Maximum number of merged entries to return.

    Returns:
        A merged list of schema summaries ranked by total count.

    Raises:
        None.

    Examples:
        .. code-block:: python

            merged = _merge_schema_ref_summaries(req, resp, limit=8)
    """
    counter: Counter[str] = Counter()

    for summary in [*request_summaries, *response_summaries]:
        counter[summary.schema_ref] += summary.count

    return [
        SchemaRefSummary(schema_ref=schema_ref, count=count)
        for schema_ref, count in counter.most_common(limit)
    ]


def _build_candidate_examples(
    candidates: list[McpCandidate],
    *,
    limit: int,
) -> list[CandidateExample]:
    """Build compact candidate examples for summarizer input.

    Args:
        candidates: Candidate MCP items.
        limit: Maximum number of examples.

    Returns:
        A list of compact candidate examples.

    Raises:
        None.

    Examples:
        .. code-block:: python

            examples = _build_candidate_examples(candidates, limit=3)
    """
    return [
        CandidateExample(
            operation_key=candidate.operation_key,
            operation_slug=candidate.operation_slug,
            kind=candidate.kind,
            title=candidate.title,
            safety_level=candidate.safety_level,
            tool_name=candidate.tool_name,
            resource_uri=candidate.resource_uri,
        )
        for candidate in candidates[:limit]
    ]


def _collect_notable_operation_keys(
    operations: Iterable[ApiOperation],
    *,
    limit: int = 8,
) -> list[str]:
    """Collect a small stable list of notable operation keys.

    Args:
        operations: Candidate operations.
        limit: Maximum number of keys to return.

    Returns:
        A short list of operation keys.

    Raises:
        None.

    Examples:
        .. code-block:: python

            keys = _collect_notable_operation_keys(catalog.operations)
    """
    return [operation.key for operation in list(operations)[:limit]]
