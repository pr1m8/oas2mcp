"""Top-level package for ``oas2mcp``."""

from oas2mcp.classify.operations import (
    classify_catalog,
    classify_operation,
)
from oas2mcp.loaders.openapi import (
    dump_openapi_spec,
    load_openapi_spec,
    load_openapi_spec_dict,
    load_openapi_spec_dict_from_file,
    load_openapi_spec_dict_from_text,
    load_openapi_spec_dict_from_url,
    load_openapi_spec_from_file,
    load_openapi_spec_from_text,
    load_openapi_spec_from_url,
)
from oas2mcp.normalize.spec_to_catalog import (
    openapi_spec_to_catalog,
    spec_dict_to_catalog,
)
from oas2mcp.viewers.summary import (
    render_catalog_summary,
    render_operation_detail,
)

__all__ = [
    "classify_catalog",
    "classify_operation",
    "dump_openapi_spec",
    "load_openapi_spec",
    "load_openapi_spec_dict",
    "load_openapi_spec_dict_from_file",
    "load_openapi_spec_dict_from_text",
    "load_openapi_spec_dict_from_url",
    "load_openapi_spec_from_file",
    "load_openapi_spec_from_text",
    "load_openapi_spec_from_url",
    "openapi_spec_to_catalog",
    "spec_dict_to_catalog",
    "render_catalog_summary",
    "render_operation_detail",
]
