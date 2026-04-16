"""Rich summary viewers for normalized OpenAPI catalogs.

Purpose:
    Render ``ApiCatalog`` and ``ApiOperation`` objects in a readable terminal
    format using Rich.

Design:
    - Focus on inspection and debugging rather than mutation.
    - Present both an overview of the whole catalog and a detailed view for
      one operation.
    - Keep rendering functions composable and CLI-friendly.

Examples:
    .. code-block:: python

        from rich.console import Console

        from oas2mcp.viewers.summary import render_catalog_summary

        render_catalog_summary(catalog, console=Console())
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from rich.box import SIMPLE_HEAVY
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from oas2mcp.models.normalized import ApiCatalog, ApiOperation, ApiParameter

_DEFAULT_MAX_PATHS: int = 25
_DEFAULT_MAX_OPERATIONS: int = 25


def render_catalog_summary(
    catalog: ApiCatalog,
    *,
    console: Console | None = None,
    max_paths: int = _DEFAULT_MAX_PATHS,
    max_operations: int = _DEFAULT_MAX_OPERATIONS,
) -> None:
    """Render a full Rich summary for an ``ApiCatalog``.

    Args:
        catalog: The normalized API catalog to display.
        console: Optional Rich console instance.
        max_paths: Maximum number of paths to display in the paths table.
        max_operations: Maximum number of operations to display in the
            operations table.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            from rich.console import Console

            render_catalog_summary(
                catalog,
                console=Console(),
            )
    """
    resolved_console = console or Console()

    resolved_console.print(build_overview_panel(catalog))
    resolved_console.print(build_info_panel(catalog))
    resolved_console.print(build_servers_table(catalog))
    resolved_console.print(build_tags_table(catalog))
    resolved_console.print(build_security_schemes_table(catalog))
    resolved_console.print(build_component_counts_table(catalog))
    resolved_console.print(build_operation_counts_table(catalog))
    resolved_console.print(build_paths_table(catalog, max_paths=max_paths))
    resolved_console.print(
        build_operations_table(catalog, max_operations=max_operations)
    )


def render_operation_detail(
    operation: ApiOperation,
    *,
    console: Console | None = None,
) -> None:
    """Render a detailed Rich view for one operation.

    Args:
        operation: The normalized operation to display.
        console: Optional Rich console instance.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            from rich.console import Console

            render_operation_detail(
                catalog.operations[0],
                console=Console(),
            )
    """
    resolved_console = console or Console()

    lines = Group(
        Text(f"{operation.method} {operation.path}", style="bold cyan"),
        Text(f"Key: {operation.key}"),
        Text(f"operationId: {operation.operation_id or '-'}"),
        Text(f"Summary: {operation.summary or '-'}"),
        Text(f"Description: {operation.description or '-'}"),
        Text(f"Tags: {', '.join(operation.tags) if operation.tags else '-'}"),
        Text(f"Deprecated: {'yes' if operation.deprecated else 'no'}"),
        Text(f"Mutating: {'yes' if operation.is_mutating else 'no'}"),
        Text(
            "External docs: "
            f"{operation.external_docs_url or '-'}"
            + (
                f" ({operation.external_docs_description})"
                if operation.external_docs_description
                else ""
            )
        ),
    )

    resolved_console.print(
        Panel(
            lines,
            title="Operation Detail",
            border_style="green",
        )
    )
    resolved_console.print(build_parameters_table(operation.parameters))
    resolved_console.print(build_request_body_table(operation))
    resolved_console.print(build_responses_table(operation))
    resolved_console.print(build_operation_security_table(operation))


def build_overview_panel(catalog: ApiCatalog) -> Panel:
    """Build a Rich overview panel for an ``ApiCatalog``.

    Args:
        catalog: The normalized API catalog.

    Returns:
        A Rich ``Panel``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            panel = build_overview_panel(catalog)
    """
    lines = Group(
        Text(f"Name: {catalog.name}", style="bold"),
        Text(f"Source: {catalog.source_uri}", style="cyan"),
        Text(f"OpenAPI Version: {catalog.openapi_version or '-'}"),
        Text(
            "Counts: "
            f"{len(catalog.servers)} servers, "
            f"{len(catalog.tags)} tags, "
            f"{len(catalog.paths)} paths, "
            f"{catalog.operation_count} operations, "
            f"{len(catalog.security_schemes)} security schemes"
        ),
    )

    return Panel(lines, title="Catalog Overview", border_style="green")


def build_info_panel(catalog: ApiCatalog) -> Panel:
    """Build a Rich info panel from the catalog metadata.

    Args:
        catalog: The normalized API catalog.

    Returns:
        A Rich ``Panel``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            panel = build_info_panel(catalog)
    """
    if catalog.info is None:
        return Panel(
            Text("No top-level info metadata was normalized.", style="dim"),
            title="Info",
            border_style="yellow",
        )

    info = catalog.info
    contact_text = "-"
    if info.contact is not None:
        pieces = [
            piece
            for piece in (info.contact.name, info.contact.email, info.contact.url)
            if piece
        ]
        contact_text = ", ".join(pieces) if pieces else "-"

    license_text = "-"
    if info.license is not None:
        pieces = [
            piece
            for piece in (
                info.license.name,
                info.license.identifier,
                info.license.url,
            )
            if piece
        ]
        license_text = ", ".join(pieces) if pieces else "-"

    lines = Group(
        Text(f"Title: {info.title}", style="bold"),
        Text(f"Version: {info.version}"),
        Text(f"Summary: {info.summary or '-'}"),
        Text(f"Description: {info.description or '-'}"),
        Text(f"Terms of Service: {info.terms_of_service or '-'}"),
        Text(f"Contact: {contact_text}"),
        Text(f"License: {license_text}"),
    )

    return Panel(lines, title="Info", border_style="blue")


def build_servers_table(catalog: ApiCatalog) -> Table:
    """Build a Rich table summarizing catalog servers.

    Args:
        catalog: The normalized API catalog.

    Returns:
        A Rich ``Table``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            table = build_servers_table(catalog)
    """
    table = Table(title="Servers", box=SIMPLE_HEAVY)
    table.add_column("#", style="dim", width=4)
    table.add_column("URL", style="cyan")
    table.add_column("Description")
    table.add_column("Variables", overflow="fold")

    if not catalog.servers:
        table.add_row("-", "[dim]No servers[/dim]", "-", "-")
        return table

    for index, server in enumerate(catalog.servers, start=1):
        variable_text = (
            ", ".join(
                f"{name}={metadata.get('default', '-')}"
                for name, metadata in server.variables.items()
            )
            if server.variables
            else "-"
        )

        table.add_row(
            str(index),
            server.url,
            server.description or "-",
            variable_text,
        )

    return table


def build_tags_table(catalog: ApiCatalog) -> Table:
    """Build a Rich table summarizing catalog tags.

    Args:
        catalog: The normalized API catalog.

    Returns:
        A Rich ``Table``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            table = build_tags_table(catalog)
    """
    table = Table(title="Tags", box=SIMPLE_HEAVY)
    table.add_column("Name", style="magenta")
    table.add_column("Description", overflow="fold")
    table.add_column("External Docs", overflow="fold")

    if not catalog.tags:
        table.add_row("[dim]No tags[/dim]", "-", "-")
        return table

    for tag in catalog.tags:
        external_docs = tag.external_docs_url or "-"
        if tag.external_docs_description:
            external_docs = f"{external_docs} ({tag.external_docs_description})"

        table.add_row(
            tag.name,
            tag.description or "-",
            external_docs,
        )

    return table


def build_security_schemes_table(catalog: ApiCatalog) -> Table:
    """Build a Rich table summarizing security schemes.

    Args:
        catalog: The normalized API catalog.

    Returns:
        A Rich ``Table``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            table = build_security_schemes_table(catalog)
    """
    table = Table(title="Security Schemes", box=SIMPLE_HEAVY)
    table.add_column("Name", style="red")
    table.add_column("Type")
    table.add_column("Details", overflow="fold")

    if not catalog.security_schemes:
        table.add_row("[dim]No security schemes[/dim]", "-", "-")
        return table

    for scheme in catalog.security_schemes:
        details = [
            f"scheme={scheme.scheme}" if scheme.scheme else None,
            f"bearer={scheme.bearer_format}" if scheme.bearer_format else None,
            f"in={scheme.location}" if scheme.location else None,
            f"name={scheme.parameter_name}" if scheme.parameter_name else None,
            (
                f"openid={scheme.open_id_connect_url}"
                if scheme.open_id_connect_url
                else None
            ),
            f"flows={', '.join(scheme.flows.keys())}" if scheme.flows else None,
        ]
        detail_text = ", ".join(item for item in details if item) or "-"

        table.add_row(
            scheme.name,
            scheme.type,
            detail_text,
        )

    return table


def build_component_counts_table(catalog: ApiCatalog) -> Table:
    """Build a Rich table summarizing component counts.

    Args:
        catalog: The normalized API catalog.

    Returns:
        A Rich ``Table``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            table = build_component_counts_table(catalog)
    """
    table = Table(title="Components", box=SIMPLE_HEAVY)
    table.add_column("Section", style="cyan")
    table.add_column("Count", justify="right")

    if not catalog.component_counts:
        table.add_row("[dim]No component counts[/dim]", "0")
        return table

    for section, count in catalog.component_counts.items():
        table.add_row(section, str(count))

    return table


def build_operation_counts_table(catalog: ApiCatalog) -> Table:
    """Build a Rich table of operation counts by HTTP method.

    Args:
        catalog: The normalized API catalog.

    Returns:
        A Rich ``Table``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            table = build_operation_counts_table(catalog)
    """
    counts = Counter(operation.method for operation in catalog.operations)

    table = Table(title="Operation Counts", box=SIMPLE_HEAVY)
    table.add_column("Method", style="yellow")
    table.add_column("Count", justify="right")

    if not counts:
        table.add_row("-", "0")
        return table

    for method, count in sorted(counts.items()):
        table.add_row(method, str(count))

    return table


def build_paths_table(catalog: ApiCatalog, *, max_paths: int) -> Table:
    """Build a Rich table summarizing normalized path items.

    Args:
        catalog: The normalized API catalog.
        max_paths: Maximum number of paths to display.

    Returns:
        A Rich ``Table``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            table = build_paths_table(catalog, max_paths=25)
    """
    table = Table(title=f"Paths (showing up to {max_paths})", box=SIMPLE_HEAVY)
    table.add_column("Path", style="cyan", overflow="fold")
    table.add_column("Methods", style="yellow")
    table.add_column("Example Summary", overflow="fold")

    if not catalog.paths:
        table.add_row("[dim]No paths[/dim]", "-", "-")
        return table

    for path_item in catalog.paths[:max_paths]:
        methods = (
            ", ".join(operation.method for operation in path_item.operations) or "-"
        )
        example_summary = (
            path_item.operations[0].summary if path_item.operations else "-"
        ) or "-"

        table.add_row(path_item.path, methods, example_summary)

    return table


def build_operations_table(
    catalog: ApiCatalog,
    *,
    max_operations: int,
) -> Table:
    """Build a Rich table summarizing normalized operations.

    Args:
        catalog: The normalized API catalog.
        max_operations: Maximum number of operations to display.

    Returns:
        A Rich ``Table``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            table = build_operations_table(catalog, max_operations=25)
    """
    table = Table(
        title=f"Operations (showing up to {max_operations})", box=SIMPLE_HEAVY
    )
    table.add_column("Method", style="yellow")
    table.add_column("Path", style="cyan", overflow="fold")
    table.add_column("operationId", overflow="fold")
    table.add_column("Tags", overflow="fold")
    table.add_column("Params", overflow="fold")
    table.add_column("Responses")
    table.add_column("Flags")

    if not catalog.operations:
        table.add_row("-", "-", "-", "-", "-", "-", "-")
        return table

    for operation in catalog.operations[:max_operations]:
        flags: list[str] = []
        if operation.is_mutating:
            flags.append("mutating")
        if operation.deprecated:
            flags.append("deprecated")

        table.add_row(
            operation.method,
            operation.path,
            operation.operation_id or "-",
            ", ".join(operation.tags) if operation.tags else "-",
            _format_parameter_summary(operation.parameters),
            ", ".join(response.status_code for response in operation.responses) or "-",
            ", ".join(flags) if flags else "-",
        )

    return table


def build_parameters_table(parameters: Iterable[ApiParameter]) -> Table:
    """Build a Rich table for normalized parameters.

    Args:
        parameters: The parameters to display.

    Returns:
        A Rich ``Table``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            table = build_parameters_table(operation.parameters)
    """
    table = Table(title="Parameters", box=SIMPLE_HEAVY)
    table.add_column("Name", style="cyan")
    table.add_column("Location")
    table.add_column("Required")
    table.add_column("Type")
    table.add_column("Default")
    table.add_column("Enum", overflow="fold")
    table.add_column("Description", overflow="fold")

    parameter_list = list(parameters)
    if not parameter_list:
        table.add_row("[dim]No parameters[/dim]", "-", "-", "-", "-", "-", "-")
        return table

    for parameter in parameter_list:
        table.add_row(
            parameter.name,
            parameter.location,
            "yes" if parameter.required else "no",
            parameter.schema_type or "-",
            repr(parameter.default) if parameter.default is not None else "-",
            (
                ", ".join(repr(item) for item in parameter.enum_values)
                if parameter.enum_values
                else "-"
            ),
            parameter.description or "-",
        )

    return table


def build_request_body_table(operation: ApiOperation) -> Table:
    """Build a Rich table for an operation request body.

    Args:
        operation: The operation to display.

    Returns:
        A Rich ``Table``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            table = build_request_body_table(operation)
    """
    table = Table(title="Request Body", box=SIMPLE_HEAVY)
    table.add_column("Required")
    table.add_column("Description", overflow="fold")
    table.add_column("Content Type", style="cyan")
    table.add_column("Schema Ref", overflow="fold")
    table.add_column("Schema Type")

    if operation.request_body is None:
        table.add_row("no", "[dim]No request body[/dim]", "-", "-", "-")
        return table

    request_body = operation.request_body
    if not request_body.media_types:
        table.add_row(
            "yes" if request_body.required else "no",
            request_body.description or "-",
            "-",
            "-",
            "-",
        )
        return table

    for media_type in request_body.media_types:
        table.add_row(
            "yes" if request_body.required else "no",
            request_body.description or "-",
            media_type.content_type,
            media_type.schema_ref or "-",
            media_type.schema_type or "-",
        )

    return table


def build_responses_table(operation: ApiOperation) -> Table:
    """Build a Rich table for normalized responses.

    Args:
        operation: The operation to display.

    Returns:
        A Rich ``Table``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            table = build_responses_table(operation)
    """
    table = Table(title="Responses", box=SIMPLE_HEAVY)
    table.add_column("Status", style="cyan")
    table.add_column("Description", overflow="fold")
    table.add_column("Content Types", overflow="fold")
    table.add_column("Schema Refs", overflow="fold")

    if not operation.responses:
        table.add_row("[dim]No responses[/dim]", "-", "-", "-")
        return table

    for response in operation.responses:
        content_types = (
            ", ".join(media_type.content_type for media_type in response.media_types)
            or "-"
        )
        schema_refs = (
            ", ".join(
                media_type.schema_ref
                for media_type in response.media_types
                if media_type.schema_ref
            )
            or "-"
        )

        table.add_row(
            response.status_code,
            response.description or "-",
            content_types,
            schema_refs,
        )

    return table


def build_operation_security_table(operation: ApiOperation) -> Table:
    """Build a Rich table for operation security requirements.

    Args:
        operation: The operation to display.

    Returns:
        A Rich ``Table``.

    Raises:
        None.

    Examples:
        .. code-block:: python

            table = build_operation_security_table(operation)
    """
    table = Table(title="Security Requirements", box=SIMPLE_HEAVY)
    table.add_column("#", style="dim", width=4)
    table.add_column("Scheme Names", overflow="fold")

    if not operation.security:
        table.add_row("-", "[dim]No security requirements[/dim]")
        return table

    for index, requirement in enumerate(operation.security, start=1):
        scheme_names = ", ".join(requirement.scheme_names) or "[anonymous]"
        table.add_row(str(index), scheme_names)

    return table


def _format_parameter_summary(parameters: list[ApiParameter]) -> str:
    """Format a compact parameter summary by location."""
    buckets: dict[str, list[str]] = {
        "path": [],
        "query": [],
        "header": [],
        "cookie": [],
    }

    for parameter in parameters:
        buckets.setdefault(parameter.location, []).append(parameter.name)

    parts = [
        f"{location}=[{', '.join(names)}]"
        for location, names in buckets.items()
        if names
    ]
    return "; ".join(parts) if parts else "-"
