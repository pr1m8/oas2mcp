"""Tests for deterministic summarizer and enhancer prompt helpers."""

from __future__ import annotations

from oas2mcp.agent.enhancer.prompts import (
    build_operation_enhancer_runtime_instruction_lines,
    build_operation_enhancer_user_prompt,
)
from oas2mcp.agent.runtime import Oas2McpRuntimeContext
from oas2mcp.agent.summarizer.prompts import (
    build_catalog_summary_runtime_instruction_lines,
    build_catalog_summary_user_prompt,
)


def test_catalog_summary_runtime_instruction_lines_reflect_runtime_settings() -> None:
    """Summary runtime instructions should reflect deterministic runtime flags."""
    runtime = Oas2McpRuntimeContext(
        source_uri="https://example.com/openapi.json",
        output_style="compact",
        include_mcp_recommendations=False,
        include_risk_notes=False,
        project_name="oas2mcp",
        user_goal="Summarize the API",
        notes=["keep it terse"],
    )

    lines = build_catalog_summary_runtime_instruction_lines(runtime)

    assert lines == [
        "Requested output style: compact.",
        "Focus first on conceptual understanding, then on light implementation implications.",
        "Do not emphasize MCP framing.",
        "Keep operational caveats minimal.",
        "Project name: oas2mcp",
        "User goal: Summarize the API",
        "Additional notes: ['keep it terse']",
    ]


def test_operation_enhancer_runtime_instruction_lines_reflect_runtime_settings() -> (
    None
):
    """Enhancer runtime instructions should reflect deterministic runtime flags."""
    runtime = Oas2McpRuntimeContext(
        source_uri="https://example.com/openapi.json",
        output_style="verbose",
        include_mcp_recommendations=True,
        include_risk_notes=True,
        project_name="oas2mcp",
        user_goal="Enhance the operation",
        notes=["prefer stable names"],
    )

    lines = build_operation_enhancer_runtime_instruction_lines(runtime)

    assert lines == [
        "Requested output style: verbose.",
        "Optimize the result for later MCP/OpenAPI export.",
        "Mention confirmation and auth considerations briefly when relevant.",
        "Project name: oas2mcp",
        "User goal: Enhance the operation",
        "Additional notes: ['prefer stable names']",
    ]


def test_user_prompts_embed_serialized_context(
    example_catalog,
    example_summary,
) -> None:
    """User prompts should embed deterministic serialized context payloads."""
    from oas2mcp.agent.enhancer.context import build_operation_enhancement_context
    from oas2mcp.agent.summarizer.context import build_catalog_summary_context
    from oas2mcp.classify.operations import classify_catalog

    bundle = classify_catalog(example_catalog)
    summary_context = build_catalog_summary_context(example_catalog, bundle=bundle)
    summary_prompt = build_catalog_summary_user_prompt(summary_context)

    assert "Catalog summary context:" in summary_prompt
    assert '"catalog_name": "Example API"' in summary_prompt
    assert '"operation_count": 4' in summary_prompt

    operation = next(
        operation
        for operation in example_catalog.operations
        if operation.operation_id == "createPet"
    )
    enhancement_context = build_operation_enhancement_context(
        catalog=example_catalog,
        bundle=bundle,
        summary=example_summary,
        operation=operation,
    )
    enhancement_prompt = build_operation_enhancer_user_prompt(enhancement_context)

    assert "Operation enhancement context:" in enhancement_prompt
    assert '"operation_id": "createPet"' in enhancement_prompt
    assert '"candidate_kind_hint": "tool"' in enhancement_prompt
