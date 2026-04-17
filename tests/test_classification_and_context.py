"""Tests for deterministic classification and context building."""

from __future__ import annotations

from oas2mcp.agent.enhancer.agent import _apply_operation_enhancement_defaults
from oas2mcp.agent.enhancer.context import build_operation_enhancement_context
from oas2mcp.agent.enhancer.models import OperationEnhancement
from oas2mcp.agent.summarizer.context import build_catalog_summary_context
from oas2mcp.classify.operations import classify_catalog
from oas2mcp.utils.lookup import get_operation_by_id


def test_classify_catalog_produces_expected_candidate_kinds(example_catalog) -> None:
    """The first-pass classifier should stay deterministic for the fixture spec."""
    bundle = classify_catalog(example_catalog)
    candidates_by_key = {
        candidate.operation_key: candidate for candidate in bundle.candidates
    }

    assert candidates_by_key["GET /inventory"].kind == "resource"
    assert candidates_by_key["GET /orders/{orderId}"].kind == "resource_template"
    assert candidates_by_key["GET /pets/{petId}"].kind == "resource_template"
    assert candidates_by_key["GET /pets/{petId}"].resource_uri is not None
    assert candidates_by_key["POST /pets"].requires_confirmation is True


def test_build_catalog_summary_context_rolls_up_fixture_counts(example_catalog) -> None:
    """Catalog summary context should expose useful top-level counts."""
    bundle = classify_catalog(example_catalog)
    context = build_catalog_summary_context(example_catalog, bundle=bundle)

    assert context.catalog_name == "Example API"
    assert context.operation_count == 4
    assert context.read_operation_count == 3
    assert context.mutating_operation_count == 1
    assert context.candidate_kind_counts["resource"] == 1
    assert any(
        summary.schema_ref.endswith("/Pet") for summary in context.primary_schema_refs
    )


def test_build_operation_enhancement_context_preserves_operation_id(
    example_catalog,
    example_summary,
) -> None:
    """Enhancer context should include the source operationId and candidate hints."""
    bundle = classify_catalog(example_catalog)
    operation = get_operation_by_id(example_catalog, operation_id="getPetById")
    assert operation is not None

    context = build_operation_enhancement_context(
        catalog=example_catalog,
        bundle=bundle,
        summary=example_summary,
        operation=operation,
    )

    assert context.operation_id == "getPetById"
    assert context.operation_slug == "getpetbyid"
    assert context.candidate_kind_hint == "resource_template"
    assert context.path_parameter_names == ["petId"]
    assert "#/components/schemas/Pet" in context.response_schema_refs


def test_operation_enhancement_defaults_fill_richer_fastmcp_fields(
    example_catalog,
    example_summary,
) -> None:
    """Post-processing should fill missing FastMCP-facing fields deterministically."""
    bundle = classify_catalog(example_catalog)
    operation = get_operation_by_id(example_catalog, operation_id="getOrderById")
    assert operation is not None
    context = build_operation_enhancement_context(
        catalog=example_catalog,
        bundle=bundle,
        summary=example_summary,
        operation=operation,
    )

    enhancement = OperationEnhancement(
        operation_key=operation.key,
        operation_id=operation.operation_id,
        operation_slug="getorderbyid",
        final_kind="resource",
        title="Get order by ID",
        description="Return a single order by its identifier.",
    )

    finalized = _apply_operation_enhancement_defaults(
        enhancement,
        context=context,
        catalog=example_catalog,
        operation=operation,
    )

    assert finalized.final_kind == "resource_template"
    assert finalized.component_name == "orders"
    assert finalized.resource_uri == "openapi://example-api/orders/{orderId}"
    assert finalized.component_meta["source_operation_id"] == "getOrderById"
    assert finalized.prompt_templates
