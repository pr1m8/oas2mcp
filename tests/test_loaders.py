"""Tests for OpenAPI loading helpers."""

from __future__ import annotations

import json

from oas2mcp.loaders.openapi import (
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
