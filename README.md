# oas2mcp

[![CI](https://github.com/pr1m8/oas2mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/pr1m8/oas2mcp/actions/workflows/ci.yml)
[![Docs](https://readthedocs.org/projects/oas2mcp/badge/?version=latest)](https://oas2mcp.readthedocs.io/en/latest/)
[![PyPI version](https://img.shields.io/pypi/v/oas2mcp.svg)](https://pypi.org/project/oas2mcp/)
[![Python versions](https://img.shields.io/pypi/pyversions/oas2mcp.svg)](https://pypi.org/project/oas2mcp/)
[![License](https://img.shields.io/pypi/l/oas2mcp.svg)](https://github.com/pr1m8/oas2mcp/blob/main/LICENSE)

Turn an OpenAPI spec into a cleaner MCP-oriented surface.

`oas2mcp` loads and normalizes OpenAPI, classifies operations into deterministic MCP hints, adds catalog- and operation-level semantic refinement, exports inspectable JSON artifacts, and bootstraps a FastMCP server from the original spec plus exported metadata.

## Why this exists

Raw OpenAPI-to-MCP conversion is useful for bootstrapping, but it usually produces a surface that is too literal.

`oas2mcp` is built to add the missing middle layer:

- normalize the source API into typed internal models
- classify likely tools, resources, and resource templates deterministically
- summarize the API at the catalog level
- refine operations one at a time for naming, descriptions, and prompt templates
- export artifacts you can inspect, diff, and reuse
- bootstrap FastMCP with exported route and naming overrides

## What you get

- Typed OpenAPI loading and normalization
- Deterministic MCP candidate generation
- Exported enhanced catalog artifacts under `data/exports/`
- FastMCP bootstrap that respects exported `final_kind` metadata
- Explicit prompt registration for exported prompt templates
- Formal pytest coverage for normalization, export helpers, orchestrator flow, and FastMCP e2e

## Install

For package usage:

```bash
pip install oas2mcp
```

For local development:

```bash
pdm install -G test -G docs
```

## Example usage

### 1. Load and inspect an OpenAPI spec

```python
from rich.console import Console

from oas2mcp import (
    classify_catalog,
    load_openapi_spec_dict_from_url,
    render_catalog_summary,
    spec_dict_to_catalog,
)

source_url = "https://petstore3.swagger.io/api/v3/openapi.json"

spec_dict = load_openapi_spec_dict_from_url(source_url)
catalog = spec_dict_to_catalog(spec_dict, source_uri=source_url)
bundle = classify_catalog(catalog)

print(catalog.name)
print(f"operations: {len(catalog.operations)}")
print(f"candidates: {len(bundle.candidates)}")

render_catalog_summary(catalog, console=Console())
```

### 2. Run the full summarize -> enhance -> export pipeline

This path requires `OPENAI_API_KEY` because it runs the catalog summarizer and operation enhancer agents.

```python
from oas2mcp.agent.orchestrator import run_and_export_oas2mcp_pipeline
from oas2mcp.agent.runtime import Oas2McpRuntimeContext

source_url = "https://petstore3.swagger.io/api/v3/openapi.json"

outputs = run_and_export_oas2mcp_pipeline(
    source_url=source_url,
    runtime_context=Oas2McpRuntimeContext(
        source_uri=source_url,
        project_name="petstore-mcp",
        user_goal="Create exported artifacts for FastMCP bootstrap.",
        output_style="compact",
        include_mcp_recommendations=True,
        include_risk_notes=False,
    ),
)

for name, path in outputs.items():
    print(name, path)
```

Typical outputs:

- `<catalog-slug>_enhanced_catalog.json`
- `<catalog-slug>_operation_notes.json`
- `<catalog-slug>_fastmcp_config.json`
- optional root snapshot: `<catalog-slug>.enhanced.json`

### 3. Bootstrap a FastMCP server from exported artifacts

```python
from oas2mcp.generate.fastmcp_app import (
    build_fastmcp_from_exported_artifacts,
    register_exported_prompts,
)

source_url = "https://petstore3.swagger.io/api/v3/openapi.json"
config_path = "data/exports/swagger-petstore-openapi-3-0_fastmcp_config.json"

mcp = build_fastmcp_from_exported_artifacts(
    source_url=source_url,
    fastmcp_config_path=config_path,
)
register_exported_prompts(mcp, config_path)
mcp.run(transport="http", port=8000)
```

The bootstrap layer now respects:

- exported OpenAPI `operationId` name overrides
- exported `final_kind` routing for tool vs resource vs resource template
- exported prompt templates registered explicitly on the server

## Environment

Copy the example env file if you want agent-driven flows or live upstream FastMCP calls:

```bash
cp .env.example .env
```

Required for summarizer and enhancer flows:

- `OPENAI_API_KEY`

Optional for LangSmith tracing and LangGraph deployment:

- `LANGSMITH_TRACING=true`
- `LANGSMITH_API_KEY`
- `LANGSMITH_PROJECT`
- `LANGSMITH_WORKSPACE_ID`
- `LANGSMITH_DEPLOYMENT_NAME`
- `LANGSMITH_ENDPOINT` for self-hosted LangSmith only

Optional for live upstream FastMCP checks:

- `UPSTREAM_BEARER_TOKEN`
- `UPSTREAM_API_KEY`
- `UPSTREAM_API_KEY_HEADER`

## Current status

- Deterministic parsing, normalization, classification, and export helpers are covered by pytest.
- FastMCP bootstrap is covered by an in-process e2e test that invokes tools, resources, resource templates, and prompts.
- The docs build runs in strict mode with `-W --keep-going`.
- Agent-driven summarizer and enhancer flows are still best treated as integration-style checks rather than pure unit tests.

## Local verification

Run the formal test suite:

```bash
pdm run pytest
```

Run the strict docs build:

```bash
rm -rf docs/source/autoapi docs/_build
pdm run sphinx-build -b html -W --keep-going docs/source docs/_build/html
```

Manual smoke checks remain available for interactive inspection:

```bash
pdm run python scripts/test_catalog_surface_planner_agent.py
pdm run python scripts/test_orchestrator.py
pdm run python scripts/test_fastmcp_bootstrap.py
pdm run python scripts/test_fastmcp_server.py
pdm run python scripts/test_fastmcp_client.py
```

## LangGraph deployment

The repo now includes a root-level `langgraph.json` and deployable graph entrypoints in
`src/oas2mcp/deploy/langgraph_app.py`.

Install the CLI group:

```bash
pdm install -G cli
```

Run the LangGraph dev server locally:

```bash
pdm run langgraph dev -c langgraph.json
```

The configured graphs are:

- `enhance_catalog`: runs the in-memory summarize/enhance/surface-planning pipeline and returns the enhanced catalog JSON
- `enhance_and_export_catalog`: runs the export pipeline and returns the written artifact paths

For deployment to LangSmith Deployments:

```bash
pdm run langgraph build -c langgraph.json -t oas2mcp
pdm run langgraph deploy -c langgraph.json
```

`langgraph deploy` can read the API key from `.env` via `LANGSMITH_API_KEY`.

## Project layout

```text
src/oas2mcp/
  loaders/       Fetch and parse OpenAPI sources
  normalize/     Convert raw specs into normalized models
  classify/      Deterministic MCP candidate generation
  agent/         Summarizer, enhancer, runtime, and orchestration
  generate/      Artifact export and FastMCP bootstrap
tests/           Formal unit and end-to-end coverage
scripts/         Manual smoke runners and local inspection helpers
docs/            Sphinx documentation published through Read the Docs
```

## Documentation and release

- Docs: `docs/source/`, published via Read the Docs
- CI: `.github/workflows/ci.yml`
- Docs validation: `.github/workflows/docs.yml`
- PyPI release: `.github/workflows/release.yml`

The release workflow is wired for GitHub Releases plus trusted publishing to PyPI.

If you have not configured a PyPI trusted publisher yet, add a repository secret
named `PYPI_API_TOKEN` and the same workflow will publish with a token instead.
