"""Operation enhancer agent.

Purpose:
    Build and execute the operation-level enhancer agent over one normalized API
    operation.

Design:
    - Use a shared thin agent factory from ``oas2mcp.agent.base``.
    - Keep enhancer-specific prompt building and context assembly local to this
      submodule.
    - Return structured output aligned with ``OperationEnhancement``.
    - Use dynamic prompt middleware for runtime-aware behavior.
    - Keep the one-operation enhancer tool-free because all required context is
      already provided directly in the prompt payload.
    - Retry once when structured output validation fails in orchestrated runs.

Examples:
    .. code-block:: python

        enhancement = run_operation_enhancer(
            catalog=catalog,
            bundle=bundle,
            summary=summary,
            operation=operation,
            runtime_context=runtime_context,
        )
"""

from __future__ import annotations

from typing import Any

from langchain.agents.structured_output import StructuredOutputValidationError

from oas2mcp.agent.base import (
    DEFAULT_MODEL_NAME,
    DEFAULT_REASONING_EFFORT,
    build_base_agent,
)
from oas2mcp.agent.enhancer.context import build_operation_enhancement_context
from oas2mcp.agent.enhancer.models import OperationEnhancement
from oas2mcp.agent.enhancer.prompts import (
    build_operation_enhancer_dynamic_prompt,
    build_operation_enhancer_user_prompt,
)
from oas2mcp.agent.runtime import Oas2McpRuntimeContext
from oas2mcp.agent.summarizer.models import CatalogSummary
from oas2mcp.models.mcp import McpBundle
from oas2mcp.models.normalized import ApiCatalog, ApiOperation

DEFAULT_ENHANCER_MODEL_NAME = DEFAULT_MODEL_NAME
DEFAULT_ENHANCER_REASONING_EFFORT = DEFAULT_REASONING_EFFORT


def build_enhancer_agent(
    *,
    model: Any | None = None,
    middleware: list[Any] | None = None,
):
    """Build the operation enhancer agent.

    Args:
        model: Optional LangChain model instance or identifier.
        middleware: Optional additional middleware.

    Returns:
        The configured enhancer agent runnable.

    Raises:
        RuntimeError: If the default OpenAI-backed model is used and no API key
            is available.
    """
    builtins: list[Any] = [
        build_operation_enhancer_dynamic_prompt(),
    ]

    return build_base_agent(
        model=model,
        response_format=OperationEnhancement,
        middleware=[*builtins, *(middleware or [])],
        tools=[],
        system_prompt="",
        model_name=DEFAULT_ENHANCER_MODEL_NAME,
        reasoning_effort=DEFAULT_ENHANCER_REASONING_EFFORT,
    )


def run_operation_enhancer(
    *,
    catalog: ApiCatalog,
    bundle: McpBundle,
    summary: CatalogSummary,
    operation: ApiOperation,
    runtime_context: Oas2McpRuntimeContext,
    model: Any | None = None,
    middleware: list[Any] | None = None,
) -> OperationEnhancement:
    """Run the enhancer for one operation and return structured output.

    Args:
        catalog: The normalized API catalog.
        bundle: The deterministic MCP bundle.
        summary: The catalog-level summary.
        operation: The operation to enhance.
        runtime_context: Runtime execution context.
        model: Optional LangChain model instance or identifier.
        middleware: Optional additional middleware.

    Returns:
        OperationEnhancement: The structured enhancement result.

    Raises:
        RuntimeError: If the default OpenAI-backed model is used and no API key
            is available, or if no structured response is returned.
    """
    enhancement_context = build_operation_enhancement_context(
        catalog=catalog,
        bundle=bundle,
        summary=summary,
        operation=operation,
    )

    enhancer_agent = build_enhancer_agent(
        model=model,
        middleware=middleware,
    )

    try:
        result = enhancer_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": build_operation_enhancer_user_prompt(
                            enhancement_context
                        ),
                    }
                ]
            },
            context=runtime_context,
        )
    except StructuredOutputValidationError:
        retry_prompt = (
            build_operation_enhancer_user_prompt(enhancement_context)
            + "\n\nReminder: return a complete structured object with the required "
            "fields operation_key, operation_slug, final_kind, title, and description."
        )
        result = enhancer_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": retry_prompt,
                    }
                ]
            },
            context=runtime_context,
        )

    structured_response = result.get("structured_response")
    if structured_response is None:
        raise RuntimeError("Operation enhancer did not return a structured_response.")
    return structured_response.model_copy(
        update={"operation_id": operation.operation_id}
    )
