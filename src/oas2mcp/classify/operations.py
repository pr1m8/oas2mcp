"""Deterministic operation classification helpers.

Purpose:
    Convert normalized API operations into first-pass MCP candidates before any
    agent enhancement step.

Design:
    - Classify each operation using stable heuristics.
    - Prefer predictable defaults over aggressive inference.
    - Attach prompt suggestions so later agents can elaborate rather than
      invent structure from scratch.

Examples:
    .. code-block:: python

        bundle = classify_catalog(catalog)
        candidate = bundle.candidates[0]
"""

from __future__ import annotations

from oas2mcp.models.mcp import (
    McpBundle,
    McpCandidate,
    McpPromptTemplate,
)
from oas2mcp.models.normalized import ApiCatalog, ApiOperation
from oas2mcp.utils.names import (
    make_catalog_slug,
    make_operation_resource_uri,
    make_operation_slug,
    make_tool_name,
)


def classify_catalog(catalog: ApiCatalog) -> McpBundle:
    """Classify all operations in a catalog.

    Args:
        catalog: The normalized API catalog.

    Returns:
        An ``McpBundle`` containing first-pass candidates.

    Raises:
        None.

    Examples:
        .. code-block:: python

            bundle = classify_catalog(catalog)
    """
    catalog_slug = make_catalog_slug(catalog.name)
    candidates = [
        classify_operation(catalog=catalog, operation=operation)
        for operation in catalog.operations
    ]

    return McpBundle(
        catalog_name=catalog.name,
        catalog_slug=catalog_slug,
        candidates=candidates,
    )


def classify_operation(*, catalog: ApiCatalog, operation: ApiOperation) -> McpCandidate:
    """Classify one operation into a first-pass MCP candidate.

    Args:
        catalog: The normalized API catalog.
        operation: The normalized API operation.

    Returns:
        A first-pass ``McpCandidate``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            candidate = classify_operation(
                catalog=catalog,
                operation=operation,
            )
    """
    operation_slug = make_operation_slug(operation)
    tool_name = make_tool_name(catalog_name=catalog.name, operation=operation)

    kind = _infer_kind(operation)
    resource_uri = (
        make_operation_resource_uri(catalog_name=catalog.name, operation=operation)
        if kind in {"resource", "resource_template"}
        else None
    )
    safety_level = _infer_safety_level(operation)
    requires_confirmation = operation.is_mutating or operation.deprecated

    auth_scheme_names = _collect_auth_scheme_names(operation)
    auth_notes = _build_auth_notes(auth_scheme_names)

    title = _build_title(operation)
    description = _build_description(operation)

    notes: list[str] = []
    if operation.deprecated:
        notes.append("Operation is deprecated.")
    if operation.request_body is not None:
        notes.append("Operation accepts a request body.")
    if auth_scheme_names:
        notes.append("Operation requires or inherits security requirements.")

    prompt_templates = _build_prompt_templates(operation_slug, title)

    return McpCandidate(
        operation_key=operation.key,
        operation_slug=operation_slug,
        kind=kind,
        title=title,
        description=description,
        safety_level=safety_level,
        requires_confirmation=requires_confirmation,
        tool_name=tool_name if kind == "tool" else None,
        resource_uri=resource_uri,
        auth_scheme_names=auth_scheme_names,
        auth_notes=auth_notes,
        prompt_templates=prompt_templates,
        notes=notes,
    )


def _infer_kind(operation: ApiOperation) -> str:
    """Infer the MCP candidate kind for an operation.

    Args:
        operation: The normalized API operation.

    Returns:
        The candidate kind.

    Raises:
        None.

    Examples:
        .. code-block:: python

            kind = _infer_kind(operation)
    """
    if operation.is_mutating:
        return "tool"

    if operation.method not in {"GET", "HEAD"}:
        return "tool"

    if operation.request_body is not None:
        return "tool"

    has_path_or_query_parameters = any(
        parameter.location in {"path", "query"} for parameter in operation.parameters
    )
    if has_path_or_query_parameters:
        return "resource_template"

    return "resource"


def _infer_safety_level(operation: ApiOperation) -> str:
    """Infer the safety level for an operation.

    Args:
        operation: The normalized API operation.

    Returns:
        The safety level.

    Raises:
        None.

    Examples:
        .. code-block:: python

            level = _infer_safety_level(operation)
    """
    if operation.method == "DELETE":
        return "destructive"
    if operation.is_mutating:
        return "mutating"
    return "safe_read"


def _collect_auth_scheme_names(operation: ApiOperation) -> list[str]:
    """Collect unique auth scheme names for an operation.

    Args:
        operation: The normalized API operation.

    Returns:
        A de-duplicated list of auth scheme names.

    Raises:
        None.

    Examples:
        .. code-block:: python

            names = _collect_auth_scheme_names(operation)
    """
    collected: list[str] = []
    for requirement in operation.security:
        for scheme_name in requirement.scheme_names:
            if scheme_name not in collected:
                collected.append(scheme_name)
    return collected


def _build_auth_notes(auth_scheme_names: list[str]) -> str | None:
    """Build a simple auth note for a candidate.

    Args:
        auth_scheme_names: The auth scheme names.

    Returns:
        A short auth note or ``None``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            note = _build_auth_notes(["api_key"])
    """
    if not auth_scheme_names:
        return None
    return f"Security schemes referenced: {', '.join(auth_scheme_names)}."


def _build_title(operation: ApiOperation) -> str:
    """Build a user-facing title for an operation candidate.

    Args:
        operation: The normalized API operation.

    Returns:
        A title string.

    Raises:
        None.

    Examples:
        .. code-block:: python

            title = _build_title(operation)
    """
    if operation.summary:
        return operation.summary
    if operation.operation_id:
        return operation.operation_id
    return f"{operation.method} {operation.path}"


def _build_description(operation: ApiOperation) -> str:
    """Build a user-facing description for an operation candidate.

    Args:
        operation: The normalized API operation.

    Returns:
        A description string.

    Raises:
        None.

    Examples:
        .. code-block:: python

            description = _build_description(operation)
    """
    if operation.description:
        return operation.description
    if operation.summary:
        return operation.summary
    return f"Execute {operation.method} against {operation.path}."


def _build_prompt_templates(operation_slug: str, title: str) -> list[McpPromptTemplate]:
    """Build first-pass prompt template suggestions.

    Args:
        operation_slug: The operation slug.
        title: The candidate title.

    Returns:
        A list of prompt templates.

    Raises:
        None.

    Examples:
        .. code-block:: python

            prompts = _build_prompt_templates("get-pet-by-id", "Get pet by ID")
    """
    return [
        McpPromptTemplate(
            name=f"explain-{operation_slug}",
            title=f"Explain {title}",
            description="Summarize what this operation does, its inputs, and its outputs.",
            arguments=["user_goal"],
            template=(
                f"Explain how to use the `{operation_slug}` operation.\n"
                "User goal: {user_goal}\n\n"
                "Describe the expected inputs, outputs, and any important caveats."
            ),
            tags=["operation", "explain"],
            meta={"generated_by": "oas2mcp", "operation_slug": operation_slug},
        ),
        McpPromptTemplate(
            name=f"draft-call-{operation_slug}",
            title=f"Draft call for {title}",
            description="Draft a safe and valid call plan for this operation.",
            arguments=["user_goal", "known_inputs"],
            template=(
                f"Draft a safe call plan for the `{operation_slug}` operation.\n"
                "User goal: {user_goal}\n"
                "Known inputs: {known_inputs}\n\n"
                "List the required parameters, optional parameters, and any "
                "confirmation or auth considerations."
            ),
            tags=["operation", "planning"],
            meta={"generated_by": "oas2mcp", "operation_slug": operation_slug},
        ),
    ]
