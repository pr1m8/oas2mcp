"""Normalized model exports for ``oas2mcp``.

Purpose:
    Expose stable Pydantic models that represent a normalized view of an
    OpenAPI specification.

Design:
    - Keep the normalized models independent from loading and rendering.
    - Provide a curated public API for downstream normalization and viewers.

Attributes:
    __all__: Curated public exports for normalized models.

Examples:
    .. code-block:: python

        from oas2mcp.models import ApiCatalog, ApiOperation
"""

from oas2mcp.models.normalized import (
    ApiCatalog,
    ApiContact,
    ApiInfo,
    ApiLicense,
    ApiMediaType,
    ApiOperation,
    ApiParameter,
    ApiPathItem,
    ApiRequestBody,
    ApiResponse,
    ApiSecurityRequirement,
    ApiSecurityScheme,
    ApiServer,
    ApiTag,
)

__all__ = [
    "ApiCatalog",
    "ApiContact",
    "ApiInfo",
    "ApiLicense",
    "ApiMediaType",
    "ApiOperation",
    "ApiParameter",
    "ApiPathItem",
    "ApiRequestBody",
    "ApiResponse",
    "ApiSecurityRequirement",
    "ApiSecurityScheme",
    "ApiServer",
    "ApiTag",
]
