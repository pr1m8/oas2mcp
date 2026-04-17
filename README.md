# oas2mcp

[![CI](https://github.com/pr1m8/oas2mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/pr1m8/oas2mcp/actions/workflows/ci.yml)
[![Docs](https://readthedocs.org/projects/oas2mcp/badge/?version=latest)](https://oas2mcp.readthedocs.io/en/latest/)
[![PyPI version](https://img.shields.io/pypi/v/oas2mcp.svg)](https://pypi.org/project/oas2mcp/)
[![Python versions](https://img.shields.io/pypi/pyversions/oas2mcp.svg)](https://pypi.org/project/oas2mcp/)
[![License](https://img.shields.io/pypi/l/oas2mcp.svg)](https://github.com/pr1m8/oas2mcp/blob/main/LICENSE)

Turn an OpenAPI spec into an inspectable, agent-refined MCP surface.

`oas2mcp` is not a raw OpenAPI-to-MCP mirror. It combines deterministic normalization and classification with a small agent pipeline that improves naming, descriptions, prompt surfaces, and shared server ergonomics before exporting artifacts for FastMCP bootstrap or LangGraph deployment.

## What the agents do

The repo now has three distinct agent stages, each with a narrow role:

- `catalog summarizer`: understands the API as a whole, including domains, authentication shape, and read/write patterns
- `operation enhancer`: refines one operation at a time for titles, descriptions, tool vs resource semantics, confirmation notes, and prompt templates
- `catalog surface planner`: designs the shared MCP layer, including catalog prompts, shared resources, and server instructions

The orchestrator keeps these stages deterministic and ordered:

1. load and normalize the source spec
2. classify deterministic MCP hints
3. summarize the catalog once
4. enhance each operation
5. plan the shared surface once
6. export inspectable artifacts
7. bootstrap FastMCP or expose the flow through LangGraph

## Why this exists

Plain OpenAPI bootstrapping is good for speed, but usually too literal for real MCP use. `oas2mcp` adds the semantic middle layer that OpenAPI specs usually lack:

- stable internal models
- deterministic candidate generation
- better tool, resource, and resource-template framing
- shared prompt and resource planning
- exported metadata you can inspect, diff, and reuse
- deployable graph wrappers around the same pipeline

## Supported source inputs

The loader accepts common OpenAPI forms directly:

- remote URLs such as `https://example.com/openapi.json`
- local files such as `openapi.yaml` or `specs/petstore.json`
- `file://` URIs
- raw JSON or YAML text
- Swagger 2.0 / OpenAPI 2 documents, normalized into the internal catalog model

## What you get

- typed OpenAPI loading and normalization
- deterministic MCP candidate generation
- three focused agent layers instead of one monolithic agent
- exported artifacts under `data/exports/`
- FastMCP bootstrap with name and kind overrides from exported metadata
- deployable LangGraph wrappers for the in-memory and export flows
- LangSmith tracing support for agent and deployment runs
- pytest coverage for normalization, export logic, FastMCP e2e behavior, and LangGraph deployment wrappers

By default, generated JSON stays under `data/exports/`. Root-level snapshot files are now opt-in only.

## Install

For package usage:

```bash
pip install oas2mcp
```

For local development:

```bash
pdm install -G test -G docs -G cli
```

The `cli` group includes the in-memory LangGraph API server extras needed for
`langgraph dev`, not just the bare CLI wrapper.

## Example usage

### 1. Load and inspect a local or remote spec

```python
from rich.console import Console

from oas2mcp import classify_catalog, load_openapi_spec_dict, render_catalog_summary
from oas2mcp.normalize.spec_to_catalog import spec_dict_to_catalog

source = "openapi.yaml"

spec_dict = load_openapi_spec_dict(source)
catalog = spec_dict_to_catalog(spec_dict, source_uri=source)
bundle = classify_catalog(catalog)

print(catalog.name)
print(f"operations: {len(catalog.operations)}")
print(f"candidates: {len(bundle.candidates)}")

render_catalog_summary(catalog, console=Console())
```

### 2. Run the full agent pipeline and export artifacts

This path requires `OPENAI_API_KEY`.

```python
from oas2mcp.agent.orchestrator import run_and_export_oas2mcp_pipeline
from oas2mcp.agent.runtime import Oas2McpRuntimeContext
from oas2mcp.generate.config import ExportConfig

source = "openapi.yaml"

outputs = run_and_export_oas2mcp_pipeline(
    source=source,
    runtime_context=Oas2McpRuntimeContext(
        source_uri=source,
        project_name="petstore-mcp",
        user_goal="Produce a clean MCP surface for deployment.",
        output_style="compact",
        include_mcp_recommendations=True,
        include_risk_notes=False,
    ),
    export_config=ExportConfig(
        export_dir="data/exports",
        write_root_snapshot=False,
    ),
)

for name, path in outputs.items():
    print(name, path)
```

Typical outputs:

- `data/exports/<catalog-slug>_enhanced_catalog.json`
- `data/exports/<catalog-slug>_operation_notes.json`
- `data/exports/<catalog-slug>_surface_plan.json`
- `data/exports/<catalog-slug>_fastmcp_config.json`

### 3. Bootstrap FastMCP from exported artifacts

```python
from oas2mcp.generate.fastmcp_app import (
    build_fastmcp_from_exported_artifacts,
    register_exported_prompts,
    register_exported_resources,
)

source = "openapi.yaml"
config_path = "data/exports/example-api_fastmcp_config.json"

mcp = build_fastmcp_from_exported_artifacts(
    source=source,
    fastmcp_config_path=config_path,
)
register_exported_resources(mcp, config_path)
register_exported_prompts(mcp, config_path)
mcp.run(transport="http", port=8000)
```

The bootstrap layer respects:

- exported name overrides keyed by OpenAPI `operationId`
- exported `final_kind` routing for tool vs resource vs resource template
- catalog-level prompts and resources from the surface planner
- server instructions derived from the shared surface plan

## LangGraph and LangSmith deployment

The repo includes deployable LangGraph wrappers in [src/oas2mcp/deploy/langgraph_app.py](src/oas2mcp/deploy/langgraph_app.py) and a deployment config at [config/langgraph.json](config/langgraph.json).

Run the LangGraph CLI commands from the repository root so the config's `./src`
and `./.env` paths resolve correctly.

The two exposed graphs are:

- `enhance_catalog`: runs the in-memory summarize -> enhance -> surface-plan flow and returns enhanced catalog JSON
- `enhance_and_export_catalog`: runs the export flow and returns written artifact paths

Run the local LangGraph dev server:

```bash
pdm run langgraph dev --config config/langgraph.json --no-browser
```

Validate the deployment config:

```bash
pdm run langgraph validate --config config/langgraph.json
```

Build or deploy:

```bash
pdm run langgraph build --config config/langgraph.json -t oas2mcp
pdm run langgraph deploy --config config/langgraph.json
```

`langgraph deploy` reads `LANGSMITH_API_KEY` from `.env`. The config is pinned to Python 3.13 so deployment matches the package runtime.

## Environment

Copy the example env file:

```bash
cp .env.example .env
```

Required for agent-driven flows:

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

## Verification

Formal test coverage:

```bash
pdm run pytest
```

The current suite covers:

- loader and normalization behavior
- deterministic export logic
- FastMCP in-process e2e behavior
- LangGraph wrapper behavior

Docs build:

```bash
rm -rf docs/source/autoapi docs/_build
pdm run sphinx-build -b html -W --keep-going docs/source docs/_build/html
```

Manual smoke checks:

```bash
pdm run python scripts/test_catalog_surface_planner_agent.py
pdm run python scripts/test_orchestrator.py
pdm run python scripts/test_fastmcp_bootstrap.py
pdm run python scripts/test_fastmcp_server.py
pdm run python scripts/test_fastmcp_client.py
```

## Project layout

```text
src/oas2mcp/
  loaders/       Fetch and parse OpenAPI sources
  normalize/     Convert raw specs into normalized models
  classify/      Deterministic MCP candidate generation
  agent/         Summarizer, enhancer, surface planner, runtime, orchestration
  deploy/        LangGraph deployment wrappers around the orchestrator
  generate/      Artifact export and FastMCP bootstrap
tests/           Unit and end-to-end coverage
scripts/         Manual smoke runners and local inspection helpers
config/          Deployment config such as LangGraph
docs/            Sphinx documentation published through Read the Docs
```

## Documentation and release

- docs source: `docs/source/`
- CI: `.github/workflows/ci.yml`
- docs validation: `.github/workflows/docs.yml`
- PyPI release: `.github/workflows/release.yml`

The release path is now tag-driven and smoother:

1. `pdm run release_bump_patch` (or `release_bump_minor` / `release_bump_major`)
2. `pdm run release_check`
3. commit and tag `vX.Y.Z`
4. push `main` and the tag

Pushing a `v*` tag triggers `.github/workflows/release.yml`, which:

- verifies the tag matches `pyproject.toml`
- runs tests
- builds docs
- builds distributions
- publishes to PyPI
- creates the GitHub Release and attaches `dist/*`

If you have not configured a PyPI trusted publisher yet, add a repository secret named `PYPI_API_TOKEN` and the same workflow can publish with a token instead.
