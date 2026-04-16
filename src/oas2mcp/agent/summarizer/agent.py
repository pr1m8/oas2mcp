"""Catalog summarizer agent.

Purpose:
    Build and execute the catalog-level summarizer agent over a normalized
    OpenAPI catalog.

Design:
    - Use a shared thin agent factory from ``oas2mcp.agent.base``.
    - Keep summarizer-specific prompt building and context assembly local to
      this submodule.
    - Return structured output aligned with ``CatalogSummary``.
    - Use dynamic prompt middleware for runtime-aware summarization behavior.

Examples:
    .. code-block:: python

        summary = run_catalog_summarizer(
            catalog=catalog,
            runtime_context=runtime_context,
        )
"""

from __future__ import annotations

from typing import Any

from oas2mcp.agent.base import (
    DEFAULT_MODEL_NAME,
    DEFAULT_REASONING_EFFORT,
    build_base_agent,
)
from oas2mcp.agent.runtime import Oas2McpRuntimeContext
from oas2mcp.agent.summarizer.context import build_catalog_summary_context
from oas2mcp.agent.summarizer.models import CatalogSummary
from oas2mcp.agent.summarizer.prompts import (
    build_catalog_summary_dynamic_prompt,
    build_catalog_summary_user_prompt,
)
from oas2mcp.classify.operations import classify_catalog
from oas2mcp.models.normalized import ApiCatalog

DEFAULT_SUMMARIZER_MODEL_NAME = DEFAULT_MODEL_NAME
DEFAULT_SUMMARIZER_REASONING_EFFORT = DEFAULT_REASONING_EFFORT


def build_catalog_summarizer_agent(
    *,
    model: Any | None = None,
    middleware: list[Any] | None = None,
):
    """Build the catalog summarizer agent.

    Args:
        model: Optional LangChain model identifier or model instance.
        middleware: Optional additional middleware.

    Returns:
        The configured LangChain agent runnable.

    Raises:
        RuntimeError: If the default OpenAI-backed model is used and no API key
            is set.
    """
    builtins: list[Any] = [
        build_catalog_summary_dynamic_prompt(),
    ]

    return build_base_agent(
        model=model,
        response_format=CatalogSummary,
        middleware=[*builtins, *(middleware or [])],
        tools=[],
        system_prompt="",
        model_name=DEFAULT_SUMMARIZER_MODEL_NAME,
        reasoning_effort=DEFAULT_SUMMARIZER_REASONING_EFFORT,
    )


def run_catalog_summarizer(
    *,
    catalog: ApiCatalog,
    runtime_context: Oas2McpRuntimeContext,
    model: Any | None = None,
    middleware: list[Any] | None = None,
) -> CatalogSummary:
    """Run the catalog summarizer and return structured output.

    Args:
        catalog: The normalized API catalog.
        runtime_context: Runtime execution context.
        model: Optional LangChain model identifier or model instance.
        middleware: Optional additional middleware.

    Returns:
        CatalogSummary: The structured summary.

    Raises:
        RuntimeError: If the default OpenAI-backed model is used and no API key
            is set, or if no structured response is returned.
    """
    bundle = classify_catalog(catalog)
    summary_context = build_catalog_summary_context(catalog, bundle=bundle)
    summarizer_agent = build_catalog_summarizer_agent(
        model=model,
        middleware=middleware,
    )

    result = summarizer_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": build_catalog_summary_user_prompt(summary_context),
                }
            ]
        },
        context=runtime_context,
    )

    structured_response = result.get("structured_response")
    if structured_response is None:
        raise RuntimeError("Catalog summarizer did not return a structured_response.")
    return structured_response
