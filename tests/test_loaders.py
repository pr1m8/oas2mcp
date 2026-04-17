"""Tests for OpenAPI loading helpers."""

from __future__ import annotations

import json

from oas2mcp.loaders.openapi import (
    load_openapi_spec_dict,
    load_openapi_spec_dict_from_file,
    load_openapi_spec_dict_from_text,
)


def test_load_openapi_spec_dict_from_text_supports_json_and_yaml() -> None:
    """JSON and YAML inputs should both parse into dictionaries."""
    json_spec = load_openapi_spec_dict_from_text(
        '{"openapi":"3.0.3","info":{"title":"JSON","version":"1"},"paths":{}}'
    )
    yaml_spec = load_openapi_spec_dict_from_text("""
openapi: 3.0.3
info:
  title: YAML
  version: "1"
paths: {}
""")

    assert json_spec["info"]["title"] == "JSON"
    assert yaml_spec["info"]["title"] == "YAML"


def test_load_openapi_spec_dict_from_file_reads_written_spec(
    tmp_path,
    example_openapi_spec,
) -> None:
    """Specs written to disk should round-trip through the file loader."""
    path = tmp_path / "openapi.json"
    path.write_text(json.dumps(example_openapi_spec), encoding="utf-8")

    loaded = load_openapi_spec_dict_from_file(path)

    assert loaded["info"]["title"] == example_openapi_spec["info"]["title"]
    assert set(loaded["paths"]) == set(example_openapi_spec["paths"])


def test_load_openapi_spec_dict_supports_local_yaml_paths(
    tmp_path,
    example_openapi_spec,
) -> None:
    """The generic loader should accept local YAML files."""
    path = tmp_path / "openapi.yaml"
    path.write_text(
        """
openapi: 3.0.3
info:
  title: Example API
  version: "1.0.0"
paths:
  /health:
    get:
      operationId: getHealth
      responses:
        "200":
          description: ok
""",
        encoding="utf-8",
    )

    loaded = load_openapi_spec_dict(path)

    assert loaded["openapi"] == "3.0.3"
    assert loaded["info"]["title"] == "Example API"
    assert "/health" in loaded["paths"]


def test_load_openapi_spec_dict_normalizes_swagger2_text() -> None:
    """Swagger 2.0 text should be upgraded into an OpenAPI-shaped mapping."""
    loaded = load_openapi_spec_dict("""
swagger: "2.0"
info:
  title: Legacy API
  version: "1.0"
host: example.com
basePath: /api
schemes: [https]
paths:
  /pets/{petId}:
    get:
      operationId: getPet
      parameters:
        - name: petId
          in: path
          required: true
          type: string
      responses:
        "200":
          description: ok
          schema:
            type: object
            properties:
              id:
                type: string
""")

    assert loaded["openapi"] == "3.0.3"
    assert loaded["servers"] == [{"url": "https://example.com/api"}]
    response = loaded["paths"]["/pets/{petId}"]["get"]["responses"]["200"]
    assert "content" in response
    assert response["content"]["application/json"]["schema"]["type"] == "object"
