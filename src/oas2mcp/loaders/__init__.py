"""Loader helpers for ``oas2mcp``.

Purpose:
    Expose functions for reading OpenAPI specifications from URLs, files,
    and raw text.

Design:
    - Keep loading side effects isolated to this package.
    - Return plain dictionaries for the initial ingestion layer.
    - Preserve compatibility aliases while the rest of the package is being
      migrated away from LangChain's ``OpenAPISpec`` object model.

Attributes:
    __all__: Curated public exports for loader helpers.

Examples:
    .. code-block:: python

        from oas2mcp.loaders import load_openapi_spec_dict_from_file

        spec_dict = load_openapi_spec_dict_from_file("openapi.json")
"""

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

__all__ = [
    "dump_openapi_spec",
    "load_openapi_spec",
    "load_openapi_spec_dict",
    "load_openapi_spec_dict_from_file",
    "load_openapi_spec_dict_from_text",
    "load_openapi_spec_dict_from_url",
    "load_openapi_spec_from_file",
    "load_openapi_spec_from_text",
    "load_openapi_spec_from_url",
]
