"""OpenAPI loading helpers.

Purpose:
    Load OpenAPI specifications from URLs, local files, or raw text into plain
    Python dictionaries.

Design:
    - Avoid runtime dependence on LangChain's ``OpenAPISpec`` parser for now.
    - Parse JSON first, then fall back to YAML.
    - Return plain dictionaries so the normalization layer can remain stable.
    - Provide backward-compatible helper names during the transition away from
      LangChain's ``OpenAPISpec`` path.

Examples:
    .. code-block:: python

        from oas2mcp.loaders.openapi import load_openapi_spec_dict_from_url

        spec_dict = load_openapi_spec_dict_from_url(
            "https://petstore3.swagger.io/api/v3/openapi.json",
        )
        print(spec_dict["openapi"])
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import yaml


def load_openapi_spec_dict_from_url(
    url: str,
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Load an OpenAPI specification dictionary from a URL.

    Args:
        url: The URL of the OpenAPI specification.
        timeout: Request timeout in seconds.

    Returns:
        The parsed OpenAPI specification as a plain dictionary.

    Raises:
        httpx.HTTPError: If the request fails.
        ValueError: If the response body is empty or cannot be parsed.

    Examples:
        .. code-block:: python

            spec_dict = load_openapi_spec_dict_from_url(
                "https://petstore3.swagger.io/api/v3/openapi.json",
            )
    """
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        response = client.get(url)
        response.raise_for_status()
        text = response.text

    return load_openapi_spec_dict_from_text(text)


def load_openapi_spec_dict_from_text(text: str) -> dict[str, Any]:
    """Load an OpenAPI specification dictionary from raw text.

    Args:
        text: Raw JSON or YAML OpenAPI text.

    Returns:
        The parsed OpenAPI specification as a plain dictionary.

    Raises:
        ValueError: If the text is empty or cannot be parsed into a dictionary.

    Examples:
        .. code-block:: python

            spec_dict = load_openapi_spec_dict_from_text(
                '{"openapi":"3.1.0","info":{"title":"A","version":"1"},"paths":{}}'
            )
    """
    if not text.strip():
        raise ValueError("OpenAPI text was empty.")

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise ValueError("Failed to parse OpenAPI text as JSON or YAML.") from exc

    if not isinstance(data, dict):
        raise ValueError("Parsed OpenAPI content was not a dictionary.")

    return data


def load_openapi_spec_dict_from_file(
    path: str | Path,
    *,
    encoding: str = "utf-8",
) -> dict[str, Any]:
    """Load an OpenAPI specification dictionary from a local file.

    Args:
        path: The file path to the OpenAPI specification.
        encoding: Text encoding used when reading the file.

    Returns:
        The parsed OpenAPI specification as a plain dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or cannot be parsed.

    Examples:
        .. code-block:: python

            spec_dict = load_openapi_spec_dict_from_file("openapi.json")
    """
    resolved_path = Path(path).expanduser().resolve()
    text = resolved_path.read_text(encoding=encoding)
    return load_openapi_spec_dict_from_text(text)


def dump_openapi_spec(spec: Any) -> dict[str, Any]:
    """Convert a spec-like object into a plain dictionary.

    Args:
        spec: A plain dictionary or model-like object.

    Returns:
        A plain dictionary representation of the spec.

    Raises:
        TypeError: If ``spec`` cannot be converted into a dictionary.

    Examples:
        .. code-block:: python

            data = dump_openapi_spec({"openapi": "3.1.0"})
            assert data["openapi"] == "3.1.0"
    """
    if isinstance(spec, dict):
        return dict(spec)

    if hasattr(spec, "model_dump"):
        dumped = spec.model_dump()
        if isinstance(dumped, dict):
            return dumped

    if hasattr(spec, "dict"):
        dumped = spec.dict()
        if isinstance(dumped, dict):
            return dumped

    raise TypeError("OpenAPI spec could not be converted into a dictionary.")


# ---------------------------------------------------------------------------
# Backward-compatible aliases
# ---------------------------------------------------------------------------


def load_openapi_spec_from_url(
    url: str,
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Backward-compatible alias for URL-based spec loading."""
    return load_openapi_spec_dict_from_url(url, timeout=timeout)


def load_openapi_spec_from_text(text: str) -> dict[str, Any]:
    """Backward-compatible alias for text-based spec loading."""
    return load_openapi_spec_dict_from_text(text)


def load_openapi_spec_from_file(
    path: str | Path,
    *,
    encoding: str = "utf-8",
) -> dict[str, Any]:
    """Backward-compatible alias for file-based spec loading."""
    return load_openapi_spec_dict_from_file(path, encoding=encoding)
