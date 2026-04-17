"""Catalog surface planner agent."""

from __future__ import annotations

from typing import Any

from langchain.agents.structured_output import StructuredOutputValidationError

from oas2mcp.agent.base import (
    DEFAULT_MODEL_NAME,
    DEFAULT_REASONING_EFFORT,
    build_base_agent,
)
from oas2mcp.agent.runtime import Oas2McpRuntimeContext
from oas2mcp.agent.surface.context import build_catalog_surface_planning_context
from oas2mcp.agent.surface.models import (
    CatalogSurfacePlan,
    CatalogSurfacePlanningContext,
    CatalogSurfacePromptPlan,
    CatalogSurfaceResourcePlan,
)
from oas2mcp.agent.surface.prompts import (
    build_catalog_surface_dynamic_prompt,
    build_catalog_surface_user_prompt,
)
from oas2mcp.generate.models import EnhancedCatalog

DEFAULT_SURFACE_MODEL_NAME = DEFAULT_MODEL_NAME
DEFAULT_SURFACE_REASONING_EFFORT = DEFAULT_REASONING_EFFORT


def build_catalog_surface_planner_agent(
    *,
    model: Any | None = None,
    middleware: list[Any] | None = None,
):
    """Build the catalog surface planner agent."""
    builtins: list[Any] = [
        build_catalog_surface_dynamic_prompt(),
    ]

    return build_base_agent(
        model=model,
        response_format=CatalogSurfacePlan,
        middleware=[*builtins, *(middleware or [])],
        tools=[],
        system_prompt="",
        model_name=DEFAULT_SURFACE_MODEL_NAME,
        reasoning_effort=DEFAULT_SURFACE_REASONING_EFFORT,
    )


def run_catalog_surface_planner(
    *,
    enhanced_catalog: EnhancedCatalog,
    runtime_context: Oas2McpRuntimeContext,
    model: Any | None = None,
    middleware: list[Any] | None = None,
) -> CatalogSurfacePlan:
    """Run the catalog surface planner and return structured output."""
    context = build_catalog_surface_planning_context(enhanced_catalog)
    planner_agent = build_catalog_surface_planner_agent(
        model=model,
        middleware=middleware,
    )

    try:
        result = planner_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": build_catalog_surface_user_prompt(context),
                    }
                ]
            },
            context=runtime_context,
        )
    except StructuredOutputValidationError:
        retry_prompt = (
            build_catalog_surface_user_prompt(context)
            + "\n\nReminder: return a complete structured object with "
            "server_instructions, catalog_prompts, catalog_resources, and notes."
        )
        result = planner_agent.invoke(
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
        raise RuntimeError(
            "Catalog surface planner did not return a structured_response."
        )

    return _apply_catalog_surface_plan_defaults(
        structured_response,
        context=context,
    )


def _apply_catalog_surface_plan_defaults(
    plan: CatalogSurfacePlan,
    *,
    context: CatalogSurfacePlanningContext,
) -> CatalogSurfacePlan:
    """Normalize planner output against deterministic default surface hints."""
    server_instructions = (
        plan.server_instructions.strip() or context.default_server_instructions
    )

    default_prompts = {
        prompt.name: prompt for prompt in context.default_catalog_prompts
    }
    merged_prompts = dict(default_prompts)
    for prompt in plan.catalog_prompts:
        default_prompt = default_prompts.get(prompt.name)
        merged_prompts[prompt.name] = _normalize_prompt_plan(
            prompt,
            default_prompt=default_prompt,
            context=context,
        )

    default_resources = {
        resource.uri: resource for resource in context.default_catalog_resources
    }
    merged_resources = dict(default_resources)
    for resource in plan.catalog_resources:
        default_resource = default_resources.get(resource.uri)
        merged_resources[resource.uri] = _normalize_resource_plan(
            resource,
            default_resource=default_resource,
            context=context,
        )

    normalized_default_prompts = [
        _normalize_prompt_plan(
            prompt,
            default_prompt=default_prompts.get(prompt.name),
            context=context,
        )
        for prompt in merged_prompts.values()
    ]
    normalized_default_resources = [
        _normalize_resource_plan(
            resource,
            default_resource=default_resources.get(resource.uri),
            context=context,
        )
        for resource in merged_resources.values()
    ]

    return plan.model_copy(
        update={
            "server_instructions": server_instructions,
            "catalog_prompts": normalized_default_prompts,
            "catalog_resources": normalized_default_resources,
        }
    )


def _normalize_prompt_plan(
    prompt: CatalogSurfacePromptPlan,
    *,
    default_prompt: CatalogSurfacePromptPlan | None,
    context: CatalogSurfacePlanningContext,
) -> CatalogSurfacePromptPlan:
    """Fill stable prompt metadata and fall back to deterministic defaults."""
    resolved_name = prompt.name or (
        default_prompt.name if default_prompt is not None else "catalog_prompt"
    )
    resolved_title = prompt.title.strip() or (
        default_prompt.title
        if default_prompt is not None
        else resolved_name.replace("_", " ").title()
    )
    resolved_description = prompt.description.strip() or (
        default_prompt.description
        if default_prompt is not None
        else "Catalog-level FastMCP prompt."
    )
    resolved_template = prompt.template.strip() or (
        default_prompt.template if default_prompt is not None else resolved_description
    )
    resolved_arguments = prompt.arguments or (
        default_prompt.arguments if default_prompt is not None else []
    )
    resolved_tags = prompt.tags or (
        default_prompt.tags if default_prompt is not None else ["catalog"]
    )
    resolved_meta = {
        "generated_by": "oas2mcp",
        "catalog_slug": context.catalog_slug,
        **(default_prompt.meta if default_prompt is not None else {}),
        **prompt.meta,
    }

    return prompt.model_copy(
        update={
            "name": resolved_name,
            "title": resolved_title,
            "description": resolved_description,
            "template": resolved_template,
            "arguments": resolved_arguments,
            "version": prompt.version
            or (default_prompt.version if default_prompt is not None else None)
            or context.catalog_version,
            "tags": resolved_tags,
            "meta": resolved_meta,
        }
    )


def _normalize_resource_plan(
    resource: CatalogSurfaceResourcePlan,
    *,
    default_resource: CatalogSurfaceResourcePlan | None,
    context: CatalogSurfacePlanningContext,
) -> CatalogSurfaceResourcePlan:
    """Fill stable resource metadata and fall back to deterministic defaults."""
    resolved_uri = resource.uri or (
        default_resource.uri if default_resource is not None else ""
    )
    resolved_name = resource.name or (
        default_resource.name if default_resource is not None else "catalog_resource"
    )
    resolved_title = resource.title.strip() or (
        default_resource.title
        if default_resource is not None
        else resolved_name.replace("_", " ").title()
    )
    resolved_description = resource.description.strip() or (
        default_resource.description
        if default_resource is not None
        else "Catalog-level FastMCP resource."
    )
    resolved_arguments = resource.arguments or (
        default_resource.arguments if default_resource is not None else []
    )
    resolved_tags = resource.tags or (
        default_resource.tags if default_resource is not None else ["catalog"]
    )
    resolved_meta = {
        "generated_by": "oas2mcp",
        "catalog_slug": context.catalog_slug,
        **(default_resource.meta if default_resource is not None else {}),
        **resource.meta,
    }
    resolved_annotations = {
        **(default_resource.annotations if default_resource is not None else {}),
        **resource.annotations,
    }

    return resource.model_copy(
        update={
            "kind": resource.kind
            or (default_resource.kind if default_resource is not None else "resource"),
            "uri": resolved_uri,
            "name": resolved_name,
            "title": resolved_title,
            "description": resolved_description,
            "mime_type": resource.mime_type
            or (
                default_resource.mime_type
                if default_resource is not None
                else "application/json"
            ),
            "handler": resource.handler
            or (default_resource.handler if default_resource is not None else "static"),
            "arguments": resolved_arguments,
            "payload": (
                resource.payload
                if resource.payload is not None
                else (
                    default_resource.payload if default_resource is not None else None
                )
            ),
            "version": resource.version
            or (default_resource.version if default_resource is not None else None)
            or context.catalog_version,
            "tags": resolved_tags,
            "meta": resolved_meta,
            "annotations": resolved_annotations,
        }
    )
