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
from oas2mcp.utils.names import make_tool_name

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
    return _apply_operation_enhancement_defaults(
        structured_response.model_copy(update={"operation_id": operation.operation_id}),
        context=enhancement_context,
        catalog=catalog,
        operation=operation,
    )


def _apply_operation_enhancement_defaults(
    enhancement: OperationEnhancement,
    *,
    context,
    catalog: ApiCatalog,
    operation: ApiOperation,
) -> OperationEnhancement:
    """Normalize agent output against deterministic enhancement hints."""
    final_kind = enhancement.final_kind
    if final_kind == "resource" and (
        context.path_parameter_names or context.query_parameter_names
    ):
        final_kind = "resource_template"

    tool_name = enhancement.tool_name
    resource_uri = enhancement.resource_uri
    if final_kind == "tool":
        tool_name = (
            tool_name
            or context.candidate_tool_name_hint
            or make_tool_name(
                catalog_name=catalog.name,
                operation=operation,
            )
        )
        resource_uri = None
    elif final_kind in {"resource", "resource_template"}:
        resource_uri = resource_uri or context.candidate_resource_uri_hint
        tool_name = None
    else:
        tool_name = None
        resource_uri = None

    component_name = enhancement.component_name or tool_name
    if component_name is None and resource_uri:
        component_name = _derive_component_name_from_uri(resource_uri)
    if component_name is None:
        component_name = context.operation_slug

    component_tags = enhancement.component_tags or _derive_component_tags(
        context=context, final_kind=final_kind
    )
    component_meta = {
        "generated_by": "oas2mcp",
        "operation_key": context.operation_key,
        "operation_slug": context.operation_slug,
        "source_operation_id": context.operation_id,
        **enhancement.component_meta,
    }

    prompt_templates = (
        enhancement.prompt_templates or context.candidate_prompt_templates
    )
    normalized_prompts = []
    for prompt in prompt_templates:
        prompt_template = prompt.template or _build_default_prompt_template(
            prompt_name=prompt.name,
            operation_slug=context.operation_slug,
            description=prompt.description,
            arguments=prompt.arguments,
        )
        prompt_tags = prompt.tags or ["operation", final_kind]
        prompt_meta = {
            "generated_by": "oas2mcp",
            "operation_slug": context.operation_slug,
            **prompt.meta,
        }
        normalized_prompts.append(
            prompt.model_copy(
                update={
                    "template": prompt_template,
                    "tags": prompt_tags,
                    "meta": prompt_meta,
                }
            )
        )

    return enhancement.model_copy(
        update={
            "final_kind": final_kind,
            "component_name": component_name,
            "tool_name": tool_name,
            "resource_uri": resource_uri,
            "component_tags": component_tags,
            "component_meta": component_meta,
            "requires_confirmation": (
                enhancement.requires_confirmation
                or context.candidate_requires_confirmation_hint
            ),
            "prompt_templates": normalized_prompts,
        }
    )


def _derive_component_tags(*, context, final_kind: str) -> list[str]:
    """Build stable default tags for exported FastMCP components."""
    tags: list[str] = []
    if context.tags:
        tags.extend(context.tags)
    if final_kind not in tags:
        tags.append(final_kind)
    if context.method.lower() not in tags:
        tags.append(context.method.lower())
    return tags


def _derive_component_name_from_uri(resource_uri: str) -> str | None:
    """Derive a stable component name from a resource URI or template."""
    uri_without_query_template = resource_uri.split("{?", 1)[0]
    _, _, path_part = uri_without_query_template.partition("://")
    if "/" in path_part:
        _, _, path_part = path_part.partition("/")
    segments = [segment for segment in path_part.split("/") if segment]
    for segment in reversed(segments):
        if not segment.startswith("{"):
            return segment
    return None


def _build_default_prompt_template(
    *,
    prompt_name: str,
    operation_slug: str,
    description: str,
    arguments: list[str],
) -> str:
    """Build a fallback prompt body when the model omitted one."""
    argument_lines = "\n".join(
        f"- {argument}: {{{argument}}}" for argument in arguments
    )
    if not argument_lines:
        argument_lines = "- no explicit arguments"

    return (
        f"{description}\n\n"
        f"Operation slug: {operation_slug}\n"
        "Arguments:\n"
        f"{argument_lines}"
    ).strip()
