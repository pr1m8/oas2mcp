"""Catalog summarizer agent submodule for ``oas2mcp``."""

from oas2mcp.agent.summarizer.agent import (
    DEFAULT_SUMMARIZER_MODEL_NAME,
    DEFAULT_SUMMARIZER_REASONING_EFFORT,
    build_catalog_summarizer_agent,
    run_catalog_summarizer,
)
from oas2mcp.agent.summarizer.context import (
    CatalogSummaryContext,
    build_catalog_summary_context,
)
from oas2mcp.agent.summarizer.models import (
    CatalogSummary,
    CatalogTagSummary,
)
from oas2mcp.agent.summarizer.prompts import (
    build_catalog_summary_dynamic_prompt,
    build_catalog_summary_system_prompt,
    build_catalog_summary_user_prompt,
)

__all__ = [
    "CatalogSummary",
    "CatalogSummaryContext",
    "CatalogTagSummary",
    "DEFAULT_SUMMARIZER_MODEL_NAME",
    "DEFAULT_SUMMARIZER_REASONING_EFFORT",
    "build_catalog_summary_context",
    "build_catalog_summary_dynamic_prompt",
    "build_catalog_summary_system_prompt",
    "build_catalog_summary_user_prompt",
    "build_catalog_summarizer_agent",
    "run_catalog_summarizer",
]
