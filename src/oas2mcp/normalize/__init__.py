"""Normalization helpers for ``oas2mcp``.

Purpose:
    Convert parsed OpenAPI specifications into stable internal Pydantic models.

Design:
    - Keep normalization logic separate from loading and rendering.
    - Accept either LangChain ``OpenAPISpec`` objects or dumped spec
      dictionaries.
    - Produce ``ApiCatalog`` objects that are easy to inspect, enrich,
      and eventually transform into MCP-oriented structures.

Attributes:
    __all__: Curated public exports for normalization helpers.

Examples:
    .. code-block:: python

        from oas2mcp.normalize import openapi_spec_to_catalog
        from oas2mcp.loaders import load_openapi_spec_from_url

        spec = load_openapi_spec_from_url(
            "https://petstore3.swagger.io/api/v3/openapi.json",
        )
        catalog = openapi_spec_to_catalog(
            spec,
            source_uri="https://petstore3.swagger.io/api/v3/openapi.json",
        )
"""

from oas2mcp.normalize.spec_to_catalog import (
    openapi_spec_to_catalog,
    spec_dict_to_catalog,
)

__all__ = [
    "openapi_spec_to_catalog",
    "spec_dict_to_catalog",
]
