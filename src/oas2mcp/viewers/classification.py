"""Rich viewers for MCP classification results.

Purpose:
    Render :class:`~oas2mcp.models.mcp.McpBundle`,
    :class:`~oas2mcp.models.mcp.McpCandidate`, and compact agent-context
    previews in a readable terminal format using Rich.

Design:
    - Keep classification output separate from raw OpenAPI catalog viewers.
    - Provide both a compact bundle summary and a detailed candidate view.
    - Optimize for readability when names and URIs are long.
    - Surface key agent-prep metadata such as auth, safety, prompts, notes,
      request refs, response refs, and resolved security details.

Examples:
    .. code-block:: python

        from rich.console import Console

        from oas2mcp.viewers.classification import render_mcp_bundle_summary

        render_mcp_bundle_summary(bundle, console=Console())
"""

from __future__ import annotations

from collections import Counter

from rich.box import SIMPLE_HEAVY
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from oas2mcp.models.mcp import McpBundle, McpCandidate
from oas2mcp.models.normalized import ApiCatalog, ApiOperation
from oas2mcp.utils.lookup import get_security_scheme
from oas2mcp.utils.refs import (
    collect_request_schema_refs,
    collect_response_schema_refs,
)


def render_mcp_bundle_summary(
    bundle: McpBundle,
    *,
    console: Console | None = None,
    max_candidates: int = 15,
) -> None:
    """Render a Rich summary for an MCP candidate bundle.

    Args:
        bundle: The MCP candidate bundle to display.
        console: Optional Rich console instance.
        max_candidates: Maximum number of candidates to display in the compact
            summary table.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            from rich.console import Console

            render_mcp_bundle_summary(
                bundle,
                console=Console(),
            )
    """
    resolved_console = console or Console()

    resolved_console.print(build_bundle_overview_panel(bundle))
    resolved_console.print(build_bundle_counts_table(bundle))
    resolved_console.print(
        build_candidate_summary_table(bundle, max_candidates=max_candidates)
    )


def render_mcp_candidate_detail(
    candidate: McpCandidate,
    *,
    console: Console | None = None,
) -> None:
    """Render a detailed Rich view for one MCP candidate.

    Args:
        candidate: The MCP candidate to display.
        console: Optional Rich console instance.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            from rich.console import Console

            render_mcp_candidate_detail(
                bundle.candidates[0],
                console=Console(),
            )
    """
    resolved_console = console or Console()

    resolved_console.print(build_candidate_overview_panel(candidate))
    resolved_console.print(build_candidate_metadata_table(candidate))
    resolved_console.print(build_candidate_prompts_table(candidate))
    resolved_console.print(build_candidate_notes_panel(candidate))


def render_operation_agent_context_preview(
    *,
    catalog: ApiCatalog,
    operation: ApiOperation,
    candidate: McpCandidate,
    console: Console | None = None,
) -> None:
    """Render a compact preview of the agent-facing operation context.

    Args:
        catalog: The normalized API catalog.
        operation: The normalized API operation.
        candidate: The first-pass MCP candidate derived from the operation.
        console: Optional Rich console instance.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            render_operation_agent_context_preview(
                catalog=catalog,
                operation=operation,
                candidate=candidate,
                console=Console(),
            )
    """
    resolved_console = console or Console()

    resolved_console.print(
        build_agent_context_overview_panel(
            catalog=catalog,
            operation=operation,
            candidate=candidate,
        )
    )
    resolved_console.print(build_agent_context_refs_table(operation=operation))
    resolved_console.print(
        build_agent_context_security_table(
            catalog=catalog,
            candidate=candidate,
        )
    )
    resolved_console.print(
        build_agent_context_rationale_panel(
            operation=operation,
            candidate=candidate,
        )
    )


def build_bundle_overview_panel(bundle: McpBundle) -> Panel:
    """Build a Rich overview panel for an MCP bundle.

    Args:
        bundle: The MCP bundle.

    Returns:
        A Rich panel.

    Raises:
        None.

    Examples:
        .. code-block:: python

            panel = build_bundle_overview_panel(bundle)
    """
    lines = Group(
        Text(f"Catalog: {bundle.catalog_name}", style="bold"),
        Text(f"Catalog Slug: {bundle.catalog_slug}", style="cyan"),
        Text(f"Candidates: {len(bundle.candidates)}"),
    )
    return Panel(lines, title="MCP Classification Overview", border_style="green")


def build_bundle_counts_table(bundle: McpBundle) -> Table:
    """Build a Rich table of candidate counts by kind and safety level.

    Args:
        bundle: The MCP bundle.

    Returns:
        A Rich table.

    Raises:
        None.

    Examples:
        .. code-block:: python

            table = build_bundle_counts_table(bundle)
    """
    kind_counts = Counter(candidate.kind for candidate in bundle.candidates)
    safety_counts = Counter(candidate.safety_level for candidate in bundle.candidates)

    table = Table(title="Candidate Counts", box=SIMPLE_HEAVY)
    table.add_column("Bucket", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Count", justify="right")

    if not bundle.candidates:
        table.add_row("-", "-", "0")
        return table

    for kind, count in sorted(kind_counts.items()):
        table.add_row("kind", kind, str(count))

    for safety, count in sorted(safety_counts.items()):
        table.add_row("safety", safety, str(count))

    return table


def build_candidate_summary_table(
    bundle: McpBundle,
    *,
    max_candidates: int,
) -> Table:
    """Build a compact candidate summary table.

    Args:
        bundle: The MCP bundle.
        max_candidates: Maximum number of candidates to display.

    Returns:
        A Rich table.

    Raises:
        None.

    Examples:
        .. code-block:: python

            table = build_candidate_summary_table(bundle, max_candidates=10)
    """
    table = Table(
        title=f"Candidates (showing up to {max_candidates})",
        box=SIMPLE_HEAVY,
    )
    table.add_column("Kind", style="magenta", width=9)
    table.add_column("Slug", style="cyan", overflow="fold", max_width=20)
    table.add_column("Title", overflow="fold", max_width=28)
    table.add_column("Safety", width=12)
    table.add_column("Confirm", width=8)
    table.add_column("Auth", overflow="fold", max_width=20)
    table.add_column("Prompts", justify="right", width=7)
    table.add_column("Tool / Resource", overflow="fold", max_width=34)

    if not bundle.candidates:
        table.add_row("-", "-", "-", "-", "-", "-", "-", "-")
        return table

    for candidate in bundle.candidates[:max_candidates]:
        auth_text = (
            ", ".join(candidate.auth_scheme_names)
            if candidate.auth_scheme_names
            else "-"
        )
        target = candidate.tool_name or candidate.resource_uri or "-"

        table.add_row(
            candidate.kind,
            candidate.operation_slug,
            candidate.title,
            candidate.safety_level,
            "yes" if candidate.requires_confirmation else "no",
            auth_text,
            str(len(candidate.prompt_templates)),
            target,
        )

    return table


def build_candidate_overview_panel(candidate: McpCandidate) -> Panel:
    """Build an overview panel for one MCP candidate.

    Args:
        candidate: The MCP candidate.

    Returns:
        A Rich panel.

    Raises:
        None.

    Examples:
        .. code-block:: python

            panel = build_candidate_overview_panel(candidate)
    """
    lines = Group(
        Text(f"{candidate.kind.upper()} · {candidate.title}", style="bold cyan"),
        Text(f"Operation Key: {candidate.operation_key}"),
        Text(f"Operation Slug: {candidate.operation_slug}"),
        Text(f"Safety: {candidate.safety_level}"),
        Text(
            f"Requires Confirmation: {'yes' if candidate.requires_confirmation else 'no'}"
        ),
        Text(f"Description: {candidate.description}"),
    )
    return Panel(lines, title="MCP Candidate Detail", border_style="blue")


def build_candidate_metadata_table(candidate: McpCandidate) -> Table:
    """Build a metadata table for one MCP candidate.

    Args:
        candidate: The MCP candidate.

    Returns:
        A Rich table.

    Raises:
        None.

    Examples:
        .. code-block:: python

            table = build_candidate_metadata_table(candidate)
    """
    table = Table(title="Metadata", box=SIMPLE_HEAVY)
    table.add_column("Field", style="cyan")
    table.add_column("Value", overflow="fold")

    auth_text = (
        ", ".join(candidate.auth_scheme_names) if candidate.auth_scheme_names else "-"
    )
    table.add_row("kind", candidate.kind)
    table.add_row("tool_name", candidate.tool_name or "-")
    table.add_row("resource_uri", candidate.resource_uri or "-")
    table.add_row("auth_scheme_names", auth_text)
    table.add_row("auth_notes", candidate.auth_notes or "-")

    return table


def build_candidate_prompts_table(candidate: McpCandidate) -> Table:
    """Build a table of suggested prompt templates for a candidate.

    Args:
        candidate: The MCP candidate.

    Returns:
        A Rich table.

    Raises:
        None.

    Examples:
        .. code-block:: python

            table = build_candidate_prompts_table(candidate)
    """
    table = Table(title="Prompt Templates", box=SIMPLE_HEAVY)
    table.add_column("Name", style="magenta", overflow="fold")
    table.add_column("Title", overflow="fold")
    table.add_column("Arguments", overflow="fold")
    table.add_column("Description", overflow="fold")

    if not candidate.prompt_templates:
        table.add_row("-", "-", "-", "-")
        return table

    for prompt in candidate.prompt_templates:
        table.add_row(
            prompt.name,
            prompt.title,
            ", ".join(prompt.arguments) if prompt.arguments else "-",
            prompt.description,
        )

    return table


def build_candidate_notes_panel(candidate: McpCandidate) -> Panel:
    """Build a notes panel for one MCP candidate.

    Args:
        candidate: The MCP candidate.

    Returns:
        A Rich panel.

    Raises:
        None.

    Examples:
        .. code-block:: python

            panel = build_candidate_notes_panel(candidate)
    """
    if not candidate.notes:
        content = Text("No notes.", style="dim")
    else:
        content = Group(*[Text(f"- {note}") for note in candidate.notes])

    return Panel(content, title="Notes", border_style="yellow")


def build_agent_context_overview_panel(
    *,
    catalog: ApiCatalog,
    operation: ApiOperation,
    candidate: McpCandidate,
) -> Panel:
    """Build an overview panel for the agent-facing operation context.

    Args:
        catalog: The normalized API catalog.
        operation: The normalized API operation.
        candidate: The MCP candidate derived from the operation.

    Returns:
        A Rich panel.

    Raises:
        None.

    Examples:
        .. code-block:: python

            panel = build_agent_context_overview_panel(
                catalog=catalog,
                operation=operation,
                candidate=candidate,
            )
    """
    lines = Group(
        Text(f"Catalog: {catalog.name}", style="bold"),
        Text(f"Operation: {operation.key}", style="cyan"),
        Text(f"operationId: {operation.operation_id or '-'}"),
        Text(f"Candidate kind: {candidate.kind}"),
        Text(f"Safety: {candidate.safety_level}"),
        Text(f"Tool name: {candidate.tool_name or '-'}"),
        Text(f"Resource URI: {candidate.resource_uri or '-'}"),
    )
    return Panel(lines, title="Agent Context Preview", border_style="green")


def build_agent_context_refs_table(*, operation: ApiOperation) -> Table:
    """Build a request-vs-response schema ref table for an operation.

    Args:
        operation: The normalized API operation.

    Returns:
        A Rich table.

    Raises:
        None.

    Examples:
        .. code-block:: python

            table = build_agent_context_refs_table(operation=operation)
    """
    request_refs = collect_request_schema_refs(operation)
    response_refs = collect_response_schema_refs(operation)

    table = Table(title="Schema Reference Split", box=SIMPLE_HEAVY)
    table.add_column("Bucket", style="cyan")
    table.add_column("Refs", overflow="fold")

    table.add_row("request", ", ".join(request_refs) if request_refs else "-")
    table.add_row("response", ", ".join(response_refs) if response_refs else "-")

    return table


def build_agent_context_security_table(
    *,
    catalog: ApiCatalog,
    candidate: McpCandidate,
) -> Table:
    """Build a table of resolved security scheme details for a candidate.

    Args:
        catalog: The normalized API catalog.
        candidate: The MCP candidate.

    Returns:
        A Rich table.

    Raises:
        None.

    Examples:
        .. code-block:: python

            table = build_agent_context_security_table(
                catalog=catalog,
                candidate=candidate,
            )
    """
    table = Table(title="Resolved Security Schemes", box=SIMPLE_HEAVY)
    table.add_column("Scheme", style="magenta")
    table.add_column("Type", width=12)
    table.add_column("Location", width=12)
    table.add_column("Parameter", overflow="fold")
    table.add_column("Details", overflow="fold")

    if not candidate.auth_scheme_names:
        table.add_row("-", "-", "-", "-", "No security schemes referenced.")
        return table

    for scheme_name in candidate.auth_scheme_names:
        scheme = get_security_scheme(catalog, name=scheme_name)
        if scheme is None:
            table.add_row(scheme_name, "-", "-", "-", "Scheme not found in catalog.")
            continue

        details: list[str] = []
        if scheme.scheme:
            details.append(f"scheme={scheme.scheme}")
        if scheme.bearer_format:
            details.append(f"bearer={scheme.bearer_format}")
        if scheme.open_id_connect_url:
            details.append(f"openid={scheme.open_id_connect_url}")
        if scheme.flows:
            details.append(f"flows={', '.join(scheme.flows.keys())}")

        table.add_row(
            scheme.name,
            scheme.type,
            scheme.location or "-",
            scheme.parameter_name or "-",
            ", ".join(details) if details else "-",
        )

    return table


def build_agent_context_rationale_panel(
    *,
    operation: ApiOperation,
    candidate: McpCandidate,
) -> Panel:
    """Build a small deterministic rationale panel for one classification.

    Args:
        operation: The normalized API operation.
        candidate: The MCP candidate derived from the operation.

    Returns:
        A Rich panel.

    Raises:
        None.

    Examples:
        .. code-block:: python

            panel = build_agent_context_rationale_panel(
                operation=operation,
                candidate=candidate,
            )
    """
    reasons: list[str] = []

    if operation.method in {"GET", "HEAD"}:
        reasons.append(f"{operation.method} is treated as read-oriented by default.")
    else:
        reasons.append(f"{operation.method} is treated as action-oriented by default.")

    if operation.is_mutating:
        reasons.append("Mutating methods default to tool classification.")
        reasons.append("Mutating operations default to confirmation enabled.")

    if operation.method == "DELETE":
        reasons.append("DELETE defaults to destructive safety level.")

    if operation.request_body is not None:
        reasons.append("Request body present, which usually favors tool execution.")

    if candidate.auth_scheme_names:
        reasons.append("Security requirements were attached to the candidate.")

    if not reasons:
        reasons.append("No special classification rules were triggered.")

    return Panel(
        Group(*[Text(f"- {reason}") for reason in reasons]),
        title="Classification Rationale",
        border_style="yellow",
    )
