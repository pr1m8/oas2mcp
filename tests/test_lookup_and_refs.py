"""Tests for normalized catalog lookup and schema-ref helpers."""

from __future__ import annotations

from oas2mcp.utils.lookup import (
    get_operation,
    get_operation_by_id,
    get_security_scheme,
    list_mutating_operations,
    list_operations_by_tag,
    list_read_operations,
)
from oas2mcp.utils.refs import (
    collect_operation_schema_refs,
    collect_request_schema_refs,
    collect_response_schema_refs,
    dereference_schema_ref,
    resolve_json_pointer,
)


def test_lookup_helpers_resolve_operations_and_security(example_catalog) -> None:
    """Lookup helpers should return stable normalized catalog slices."""
    by_path = get_operation(example_catalog, method="get", path="pets/{petId}")
    by_id = get_operation_by_id(example_catalog, operation_id="getPetById")

    assert by_path is not None
    assert by_id is by_path
    assert by_path.path == "/pets/{petId}"
    assert by_path.method == "GET"

    pet_operations = list_operations_by_tag(example_catalog, tag="pet")
    assert {operation.operation_id for operation in pet_operations} == {
        "getPetById",
        "createPet",
    }

    assert {
        operation.operation_id
        for operation in list_mutating_operations(example_catalog)
    } == {"createPet"}
    assert {
        operation.operation_id for operation in list_read_operations(example_catalog)
    } == {
        "getInventory",
        "getOrderById",
        "getPetById",
    }

    scheme = get_security_scheme(example_catalog, name="api_key")
    assert scheme is not None
    assert scheme.location == "header"
    assert scheme.parameter_name == "X-API-Key"


def test_schema_ref_helpers_collect_and_dereference(example_catalog) -> None:
    """Schema helpers should collect unique refs and resolve local pointers."""
    create_pet = get_operation_by_id(example_catalog, operation_id="createPet")
    get_inventory = get_operation_by_id(example_catalog, operation_id="getInventory")

    assert create_pet is not None
    assert get_inventory is not None

    assert collect_request_schema_refs(create_pet) == ["#/components/schemas/Pet"]
    assert collect_response_schema_refs(create_pet) == ["#/components/schemas/Pet"]
    assert collect_operation_schema_refs(create_pet) == ["#/components/schemas/Pet"]

    assert collect_request_schema_refs(get_inventory) == []
    assert collect_response_schema_refs(get_inventory) == [
        "#/components/schemas/Inventory"
    ]

    pet_schema = dereference_schema_ref(
        example_catalog.raw_spec,
        "#/components/schemas/Pet",
    )
    assert pet_schema is not None
    assert pet_schema["type"] == "object"
    assert sorted(pet_schema["properties"]) == ["id", "name"]


def test_resolve_json_pointer_supports_lists_and_escaped_segments() -> None:
    """JSON-pointer resolution should handle list indexes and escaped tokens."""
    document = {
        "components": {
            "schemas": {
                "Pet/List": {"type": "array"},
                "Pet~Meta": {"type": "object"},
            }
        },
        "items": [{"name": "first"}, {"name": "second"}],
    }

    assert resolve_json_pointer(document, "#/items/1/name") == "second"
    assert (
        resolve_json_pointer(
            document,
            "#/components/schemas/Pet~1List/type",
        )
        == "array"
    )
    assert (
        resolve_json_pointer(
            document,
            "#/components/schemas/Pet~0Meta/type",
        )
        == "object"
    )
    assert resolve_json_pointer(document, "#/items/10") is None
    assert resolve_json_pointer(document, "components/schemas/Pet") is None
