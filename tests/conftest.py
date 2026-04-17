"""Shared pytest fixtures for ``oas2mcp`` tests."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import httpx
import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from oas2mcp.agent.enhancer.models import (
    EnhancementPromptCandidate,
    OperationEnhancement,
)
from oas2mcp.agent.summarizer.models import CatalogSummary, CatalogTagSummary
from oas2mcp.generate.models import EnhancedCatalog
from oas2mcp.normalize.spec_to_catalog import spec_dict_to_catalog

EXAMPLE_SOURCE_URI = "https://example.com/openapi.json"
EXAMPLE_SERVER_URL = "https://example.com"


def build_example_openapi_spec() -> dict[str, Any]:
    """Return a compact OpenAPI document used across tests."""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Example API",
            "version": "1.0.0",
            "description": "An example API for deterministic tests.",
        },
        "servers": [{"url": EXAMPLE_SERVER_URL}],
        "components": {
            "securitySchemes": {
                "api_key": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                }
            },
            "schemas": {
                "Pet": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                    },
                    "required": ["name"],
                },
                "Order": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "status": {"type": "string"},
                    },
                    "required": ["id"],
                },
                "Inventory": {
                    "type": "object",
                    "additionalProperties": {"type": "integer"},
                },
            },
        },
        "paths": {
            "/inventory": {
                "get": {
                    "operationId": "getInventory",
                    "summary": "Get inventory",
                    "tags": ["store"],
                    "security": [{"api_key": []}],
                    "responses": {
                        "200": {
                            "description": "Inventory counts",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Inventory"}
                                }
                            },
                        }
                    },
                }
            },
            "/orders/{orderId}": {
                "get": {
                    "operationId": "getOrderById",
                    "summary": "Get order by ID",
                    "tags": ["store"],
                    "parameters": [
                        {
                            "name": "orderId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Order details",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Order"}
                                }
                            },
                        }
                    },
                }
            },
            "/pets/{petId}": {
                "get": {
                    "operationId": "getPetById",
                    "summary": "Get pet by ID",
                    "tags": ["pet"],
                    "parameters": [
                        {
                            "name": "petId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Pet details",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Pet"}
                                }
                            },
                        }
                    },
                }
            },
            "/pets": {
                "post": {
                    "operationId": "createPet",
                    "summary": "Create pet",
                    "tags": ["pet"],
                    "security": [{"api_key": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Pet"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Created pet",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Pet"}
                                }
                            },
                        }
                    },
                }
            },
        },
    }


@pytest.fixture
def example_openapi_spec() -> dict[str, Any]:
    """Provide the shared example OpenAPI specification."""
    return build_example_openapi_spec()


@pytest.fixture
def example_catalog(example_openapi_spec: dict[str, Any]):
    """Provide the normalized catalog for the shared example spec."""
    return spec_dict_to_catalog(
        example_openapi_spec,
        source_uri=EXAMPLE_SOURCE_URI,
    )


@pytest.fixture
def example_summary() -> CatalogSummary:
    """Provide a stable catalog summary for non-LLM tests."""
    return CatalogSummary(
        catalog_name="Example API",
        api_purpose="Manage pets, orders, and store inventory.",
        conceptual_overview="A small CRUD-style API with read and write flows.",
        primary_domains=[
            CatalogTagSummary(
                tag_name="store",
                description="Inventory and order endpoints.",
                operation_count=2,
                read_operation_count=2,
            ),
            CatalogTagSummary(
                tag_name="pet",
                description="Pet lookup and creation.",
                operation_count=2,
                read_operation_count=1,
                mutating_operation_count=1,
            ),
        ],
        data_model_summary="The core schemas are Pet, Order, and Inventory.",
        data_flow_summary="Inventory and order reads complement pet lookup and pet creation.",
        authentication_summary="An API key protects inventory reads and pet creation.",
        operational_notes=["Optimized for deterministic fixture-driven tests."],
        recommended_mcp_surface="Expose inventory as a resource and write flows as tools.",
        suggested_tool_domains=["pet"],
        suggested_resource_domains=["store"],
    )


@pytest.fixture
def example_enhanced_catalog(example_summary: CatalogSummary) -> EnhancedCatalog:
    """Provide a stable enhanced catalog for export and FastMCP tests."""
    return EnhancedCatalog(
        source_url=EXAMPLE_SOURCE_URI,
        catalog_name="Example API",
        catalog_slug="example-api",
        catalog_version="1.0.0",
        summary=example_summary,
        operations=[
            OperationEnhancement(
                operation_key="GET /inventory",
                operation_id="getInventory",
                operation_slug="getinventory",
                final_kind="resource",
                namespace="store",
                title="Get inventory",
                description="Return inventory counts by status.",
                component_name="inventory",
                resource_uri="openapi://example-api/inventory",
                component_tags=["store", "read"],
                component_meta={"generated_by": "fixture"},
                prompt_templates=[
                    EnhancementPromptCandidate(
                        name="view_inventory",
                        title="View inventory",
                        description="Summarize the current inventory counts.",
                        template=(
                            "Summarize the current inventory counts.\n"
                            "User goal: {user_goal}"
                        ),
                        arguments=["user_goal"],
                    )
                ],
            ),
            OperationEnhancement(
                operation_key="GET /orders/{orderId}",
                operation_id="getOrderById",
                operation_slug="getorderbyid",
                final_kind="resource_template",
                namespace="store",
                title="Get order by ID",
                description="Return a single order by its identifier.",
                component_name="order_details",
                resource_uri="openapi://example-api/orders/{orderId}",
                component_tags=["store", "read"],
                prompt_templates=[
                    EnhancementPromptCandidate(
                        name="lookup_order",
                        title="Look up order",
                        description="Prepare a lookup for a single order.",
                        arguments=["orderId"],
                        template=(
                            "Prepare a lookup for one order.\n" "Order ID: {orderId}"
                        ),
                    )
                ],
            ),
            OperationEnhancement(
                operation_key="GET /pets/{petId}",
                operation_id="getPetById",
                operation_slug="getpetbyid",
                final_kind="tool",
                namespace="pet",
                title="Get pet by ID",
                description="Fetch one pet by identifier.",
                tool_name="pet_by_id",
            ),
            OperationEnhancement(
                operation_key="POST /pets",
                operation_id="createPet",
                operation_slug="createpet",
                final_kind="tool",
                namespace="pet",
                title="Create pet",
                description="Create a pet record.",
                tool_name="create_pet",
                component_tags=["pet", "write"],
                requires_confirmation=True,
                prompt_templates=[
                    EnhancementPromptCandidate(
                        name="draft_pet_creation",
                        title="Draft pet creation",
                        description="Draft a pet creation request.",
                        arguments=["name"],
                        template="Draft a pet creation request for {name}.",
                    )
                ],
            ),
        ],
        notes=["Fixture-generated enhanced catalog."],
    )


def _build_upstream_app() -> Starlette:
    """Create a local ASGI app that mirrors the example OpenAPI spec."""

    async def get_inventory(_: Request) -> JSONResponse:
        return JSONResponse({"available": 3, "pending": 1})

    async def get_order(request: Request) -> JSONResponse:
        return JSONResponse(
            {
                "id": request.path_params["orderId"],
                "status": "ready",
            }
        )

    async def get_pet(request: Request) -> JSONResponse:
        return JSONResponse(
            {
                "id": request.path_params["petId"],
                "name": "Comet",
            }
        )

    async def create_pet(request: Request) -> JSONResponse:
        payload = await request.json()
        return JSONResponse(
            {
                "id": payload.get("id", "generated"),
                "name": payload["name"],
            }
        )

    return Starlette(
        routes=[
            Route("/inventory", get_inventory, methods=["GET"]),
            Route("/orders/{orderId}", get_order, methods=["GET"]),
            Route("/pets/{petId}", get_pet, methods=["GET"]),
            Route("/pets", create_pet, methods=["POST"]),
        ]
    )


@pytest.fixture
def upstream_app() -> Starlette:
    """Provide the local upstream ASGI application."""
    return _build_upstream_app()


@pytest.fixture
def upstream_client(upstream_app: Starlette) -> Iterator[httpx.AsyncClient]:
    """Provide an async client that targets the local upstream ASGI app."""
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=upstream_app),
        base_url=EXAMPLE_SERVER_URL,
    )
    try:
        yield client
    finally:
        import asyncio

        asyncio.run(client.aclose())
