"""Tests for LangGraph deployment wrappers."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from oas2mcp.deploy.langgraph_app import (
    enhance_and_export_catalog_graph,
    enhance_catalog_graph,
)


def test_langgraph_json_declares_repo_graphs() -> None:
    """The deployment config should point at the repo graph wrappers."""
    config = json.loads(Path("config/langgraph.json").read_text(encoding="utf-8"))

    assert config["python_version"] == "3.13"
    assert config["dependencies"] == ["."]
    assert config["env"] == "./.env"
    assert set(config["graphs"]) == {
        "enhance_catalog",
        "enhance_and_export_catalog",
    }
    assert config["graphs"]["enhance_catalog"].startswith(
        "./src/oas2mcp/deploy/langgraph_app.py:"
    )


def test_cli_dependency_group_includes_inmem_langgraph_server() -> None:
    """The CLI dependency group should support ``langgraph dev`` directly."""
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    cli_group = pyproject["dependency-groups"]["cli"]

    assert "langgraph-cli[inmem]>=0.2.11" in cli_group


def test_enhance_catalog_graph_invokes_pipeline(monkeypatch) -> None:
    """The deployment graph should return an enhanced catalog payload."""
    monkeypatch.setattr(
        "oas2mcp.deploy.langgraph_app.run_oas2mcp_pipeline",
        lambda **kwargs: _FakeCatalog(
            {
                "catalog_slug": "example-api",
                "source_url": kwargs["source"],
                "user_goal": kwargs["runtime_context"].user_goal,
            }
        ),
    )

    result = enhance_catalog_graph.invoke(
        {
            "source": "https://example.com/openapi.yaml",
            "user_goal": "Deploy this as a LangGraph app.",
        }
    )

    assert result["result"]["catalog_slug"] == "example-api"
    assert result["result"]["source_url"] == "https://example.com/openapi.yaml"
    assert result["result"]["user_goal"] == "Deploy this as a LangGraph app."


def test_enhance_and_export_catalog_graph_invokes_export_pipeline(monkeypatch) -> None:
    """The deployment graph should return exported artifact paths as strings."""
    monkeypatch.setattr(
        "oas2mcp.deploy.langgraph_app.run_and_export_oas2mcp_pipeline",
        lambda **kwargs: {
            "enhanced_catalog": Path("/tmp/example_enhanced_catalog.json"),
            "fastmcp_config": Path("/tmp/example_fastmcp_config.json"),
        },
    )

    result = enhance_and_export_catalog_graph.invoke(
        {
            "source": "https://example.com/openapi.yaml",
            "export_dir": "data/exports",
            "write_surface_plan": True,
        }
    )

    assert result["outputs"] == {
        "enhanced_catalog": "/tmp/example_enhanced_catalog.json",
        "fastmcp_config": "/tmp/example_fastmcp_config.json",
    }


class _FakeCatalog:
    """Minimal stand-in for ``EnhancedCatalog`` in deployment tests."""

    def __init__(self, payload: dict[str, str]) -> None:
        self._payload = payload

    def model_dump(self, *, mode: str = "python") -> dict[str, str]:
        assert mode == "json"
        return dict(self._payload)
