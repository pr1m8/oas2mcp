"""Utility helpers for ``oas2mcp``.

Purpose:
    Expose small, reusable helpers for catalog lookup, naming, and JSON
    pointer / ``$ref`` resolution.

Design:
    - Keep these helpers pure and side-effect free.
    - Make them easy to reuse from classifiers, viewers, and future agents.

Attributes:
    __all__: Curated public exports for the utility layer.

Examples:
    .. code-block:: python

        from oas2mcp.utils import get_operation, make_operation_slug
"""

from oas2mcp.utils.lookup import (
    get_operation,
    get_operation_by_id,
    get_security_scheme,
    list_mutating_operations,
    list_operations_by_tag,
    list_read_operations,
)
from oas2mcp.utils.names import (
    make_catalog_slug,
    make_operation_slug,
    make_resource_uri,
    make_tag_slug,
    make_tool_name,
    slugify,
)
from oas2mcp.utils.refs import (
    collect_operation_schema_refs,
    dereference_schema_ref,
    resolve_json_pointer,
)

__all__ = [
    "collect_operation_schema_refs",
    "dereference_schema_ref",
    "get_operation",
    "get_operation_by_id",
    "get_security_scheme",
    "list_mutating_operations",
    "list_operations_by_tag",
    "list_read_operations",
    "make_catalog_slug",
    "make_operation_slug",
    "make_resource_uri",
    "make_tag_slug",
    "make_tool_name",
    "resolve_json_pointer",
    "slugify",
]
