# AGENTS.md

## Purpose

This repository turns a source OpenAPI document into a more MCP-friendly surface in stages:

1. load and normalize the source OpenAPI spec
2. classify operations into first-pass MCP candidates
3. summarize the API at the catalog level
4. enhance each operation one-by-one
5. export enhanced artifacts
6. bootstrap FastMCP from the original OpenAPI plus exported metadata
7. later, generate a richer enhanced OpenAPI JSON and stronger FastMCP configuration

Treat this file as the main orientation guide for coding agents working in this repo.

## What this codebase is trying to do

The goal is **not** just to mirror a raw OpenAPI spec into MCP.
The goal is to:

- understand the API at a high level
- improve naming and descriptions
- separate read-oriented surfaces from action-oriented surfaces
- generate stable tool/resource/prompt metadata
- export artifacts that can later drive FastMCP bootstrapping and eventually a richer generated interface

The current philosophy is:

- keep the summarizer focused on the **shape of the API**
- keep the enhancer focused on **one operation at a time**
- keep the orchestrator focused on **deterministic batch execution**
- keep FastMCP bootstrapping separate from richer future rewriting/export steps

## Current architecture

### Core pipeline

The current end-to-end pipeline is:

```text
source OpenAPI URL
-> load raw spec
-> normalize into ApiCatalog
-> classify deterministic MCP candidates
-> run catalog summarizer once
-> run enhancer once per operation
-> collect EnhancedCatalog
-> export JSON artifacts
-> bootstrap FastMCP from original OpenAPI + exported metadata
```

### Main subpackages

#### `src/oas2mcp/loaders/`

Responsible for fetching and parsing OpenAPI sources.

#### `src/oas2mcp/models/`

Holds normalized and MCP-oriented models.
This is where the core typed data model lives.

#### `src/oas2mcp/normalize/`

Converts raw OpenAPI documents into normalized internal catalog structures.

#### `src/oas2mcp/classify/`

Builds deterministic MCP candidates from normalized operations.
This is a first-pass heuristic layer, not the final enhancement layer.

#### `src/oas2mcp/agent/`

Contains agent-oriented workflow logic.

Current major areas:

- `runtime.py`: runtime context
- `state.py`: typed workflow state
- `base.py`: shared model + `create_agent(...)` construction
- `summarizer/`: catalog-level understanding
- `enhancer/`: one-operation refinement
- `orchestrator.py`: summarize once, enhance all, export

#### `src/oas2mcp/generate/`

Contains export/bootstrap logic.

Current major areas:

- `models.py`: exported enhanced catalog model(s)
- `config.py`: export configuration
- `export.py`: artifact writing helpers
- `fastmcp_app.py`: FastMCP bootstrap from exported artifacts

#### `scripts/`

Development scripts for manual testing.
This repo currently relies heavily on explicit smoke-test scripts.

## Current workflow responsibilities

### Summarizer

The summarizer should answer:

- what is this API for?
- what are its major domains?
- how does its data model work?
- what is the high-level read/write shape?
- what is the light MCP framing?

The summarizer should **not**:

- write a giant risk memo
- design the entire MCP interface in detail
- generate implementation-heavy instructions
- produce deployment steps
- generate lots of prompts

The summarizer is a **landscape/overview agent**.

### Enhancer

The enhancer should answer, for **one operation at a time**:

- what should this operation be called?
- what is the best title/description?
- should it ultimately behave like a tool or resource?
- what confirmation or auth notes matter?
- what prompt template is useful, if any?

The enhancer should **not** redesign the whole API.
It works from:

- normalized operation data
- deterministic MCP candidate hints
- resolved schemas
- security schemes
- catalog summary context

### Orchestrator

The orchestrator should remain mostly deterministic.
For now it should:

- load once
- summarize once
- enhance all operations in a loop
- export artifacts

Do not make the orchestrator overly agentic unless there is a strong reason.
It is currently better as reliable pipeline glue than as a free-form decision-making agent.

## Important design principles

### 1. Deterministic first, agentic second

Always prefer deterministic transforms when possible.
Use agents to improve semantics and usability, not to replace parsing or classification that can be done deterministically.

### 2. Treat deterministic classification as a hint

Candidate values such as kind, tool name, confirmation requirement, and resource URI are **hints** for the enhancer, not final truth.

### 3. Preserve provenance

Whenever possible, keep enough information to trace an enhanced operation back to:

- source URL
- OpenAPI `operationId`
- method + path
- normalized operation key
- exported FastMCP/OpenAPI mapping

### 4. Keep role boundaries clean

Avoid mixing responsibilities across modules.
In particular:

- summarizer should not do creator/export work
- enhancer should not do catalog summarization work
- FastMCP bootstrap should not silently become a full enhanced OpenAPI rewriter

### 5. Favor explicit tests and artifacts

This repo benefits from visible intermediate artifacts.
Prefer writing test scripts and JSON exports that let humans inspect results.

## Expected file layout

A typical high-value change will touch one of these areas:

### Summarizer files

- `src/oas2mcp/agent/summarizer/models.py`
- `src/oas2mcp/agent/summarizer/context.py`
- `src/oas2mcp/agent/summarizer/prompts.py`
- `src/oas2mcp/agent/summarizer/agent.py`

### Enhancer files

- `src/oas2mcp/agent/enhancer/models.py`
- `src/oas2mcp/agent/enhancer/context.py`
- `src/oas2mcp/agent/enhancer/prompts.py`
- `src/oas2mcp/agent/enhancer/agent.py`
- `src/oas2mcp/agent/enhancer/tools.py`

### Orchestration / export files

- `src/oas2mcp/agent/orchestrator.py`
- `src/oas2mcp/generate/config.py`
- `src/oas2mcp/generate/export.py`
- `src/oas2mcp/generate/fastmcp_app.py`

### Manual scripts

- `scripts/test_catalog_summarizer_agent.py`
- `scripts/test_operation_enhancer_context.py`
- `scripts/test_operation_enhancer_agent.py`
- `scripts/test_orchestrator.py`
- `scripts/test_fastmcp_bootstrap.py`
- `scripts/test_fastmcp_server.py`
- `scripts/test_fastmcp_client.py`

## How to navigate the codebase quickly

### If you need to understand the high-level data model

Start here:

- `src/oas2mcp/models/normalized.py`
- `src/oas2mcp/models/mcp.py`
- `src/oas2mcp/generate/models.py`

### If you need to understand how OpenAPI is loaded and normalized

Start here:

- `src/oas2mcp/loaders/openapi.py`
- `src/oas2mcp/normalize/spec_to_catalog.py`

### If you need to understand MCP candidate generation

Start here:

- `src/oas2mcp/classify/operations.py`

### If you need to understand summarization

Start here:

- `src/oas2mcp/agent/summarizer/context.py`
- `src/oas2mcp/agent/summarizer/prompts.py`
- `src/oas2mcp/agent/summarizer/agent.py`

### If you need to understand operation enhancement

Start here:

- `src/oas2mcp/agent/enhancer/context.py`
- `src/oas2mcp/agent/enhancer/models.py`
- `src/oas2mcp/agent/enhancer/prompts.py`
- `src/oas2mcp/agent/enhancer/agent.py`

### If you need to understand end-to-end orchestration

Start here:

- `src/oas2mcp/agent/orchestrator.py`
- `src/oas2mcp/generate/export.py`
- `src/oas2mcp/generate/fastmcp_app.py`

## Current artifact flow

The orchestrator currently exports JSON artifacts.
Typical outputs include:

- `data/exports/<catalog-slug>_enhanced_catalog.json`
- `data/exports/<catalog-slug>_operation_notes.json`
- `data/exports/<catalog-slug>_fastmcp_config.json`
- optional project-root snapshot: `<catalog-slug>.enhanced.json`

These are important debugging artifacts.
Do not remove them casually.

## FastMCP integration guidance

FastMCP supports bootstrapping from OpenAPI with `FastMCP.from_openapi(...)`. OpenAI/Codex-style guidance files and the broader AGENTS.md ecosystem both emphasize including clear repo navigation, test commands, and conventions for coding agents. Codex specifically supports repository `AGENTS.md` files and applies them by directory scope. citeturn539862search0turn539862search2turn539862search3

Important FastMCP notes for this repo:

- default OpenAPI bootstrap maps all routes to tools unless you provide route maps
- GET endpoints should usually be restored to resources or resource templates via semantic route maps
- name overrides should be driven by exported config keyed appropriately for the bootstrap layer
- prompts are not created automatically; they need to be registered explicitly

Use bootstrap for quick validation, then move toward richer generated/exported surfaces later. FastMCP’s own docs describe raw OpenAPI conversion as best for bootstrapping/prototyping, with curated servers usually better long term. citeturn539862search0

## Environment and configuration

### Required env

At minimum, the agent workflows expect:

- `OPENAI_API_KEY`

### Optional upstream testing env

For testing upstream API calls through FastMCP:

- `UPSTREAM_BEARER_TOKEN`
- `UPSTREAM_API_KEY`
- `UPSTREAM_API_KEY_HEADER`

### Export config

Use `ExportConfig` to control where artifacts are written.
Preferred behavior:

- canonical artifacts under `data/exports/`
- optional root-level snapshot for convenience

## Commands agents should run

### Basic smoke tests

Run these when working on the summarizer:

```bash
pdm run python scripts/test_catalog_summarizer_agent.py
```

Run these when working on enhancer context:

```bash
pdm run python scripts/test_operation_enhancer_context.py
```

Run these when working on the enhancer agent:

```bash
pdm run python scripts/test_operation_enhancer_agent.py
```

Run these when working on the full summarize + enhance pipeline:

```bash
pdm run python scripts/test_orchestrator.py
```

Run these when working on FastMCP bootstrap:

```bash
pdm run python scripts/test_fastmcp_bootstrap.py
pdm run python scripts/test_fastmcp_server.py
pdm run python scripts/test_fastmcp_client.py
```

### Dependency management

This project uses **PDM**.
Do not default to `pip` unless there is a very specific reason.

Use commands like:

```bash
pdm add <package>
pdm remove <package>
pdm run python <script>
pdm install
```

## Coding conventions for this repo

### General Python style

- Use full type hints.
- Prefer clean, explicit data flow.
- Keep helper layers thin.
- Avoid hidden network calls in generic utilities.
- Separate deterministic data-building from LLM/agent execution.

### Docstrings

- Every file should start with a Google-style module docstring.
- Public classes and functions should use Google-style docstrings.
- Prefer minimal, realistic examples.

### Pydantic

- Prefer explicit `BaseModel`-style typed models where appropriate.
- Keep exported models stable and inspectable.
- Avoid field names that shadow framework/model attributes.

### Naming

- Use `*_hint` names for deterministic candidate values that the enhancer may override.
- Use `Context` suffixes for deterministic prompt/input payloads.
- Use `Enhancement` / `Summary` suffixes for structured outputs.

## What to avoid

### Do not over-agentify the orchestrator

The orchestrator is currently pipeline glue.
Do not turn it into a large tool-calling decision engine unless there is clear value.

### Do not overcomplicate the summarizer

The summarizer should not:

- produce large risk essays
- generate a giant MCP design plan
- include prompt packs or deployment steps

### Do not add complex tool schemas too early

For single-operation enhancer runs, complex state-inspection tools can create schema issues with model providers.
Keep the first enhancer versions tool-free unless a tool is clearly necessary.

### Do not silently conflate tool/resource semantics

If an operation is ultimately a tool, be careful about attaching resource-like fields unless they are clearly internal provenance rather than final output semantics.

## Current known next steps

1. improve FastMCP bootstrap so exported names and route maps are fully reflected
2. register exported prompts on the FastMCP server
3. test real endpoint calls through the FastMCP client
4. generate a richer enhanced OpenAPI JSON
5. add a creator/exporter layer that translates `EnhancedCatalog` into a more final surface
6. optionally add nested AGENTS.md files later if subpackages diverge in conventions

## Guidance for future changes

When making changes, prefer this order:

1. make the smallest deterministic improvement possible
2. add or update a focused smoke test script
3. inspect JSON artifacts
4. only then expand agent behavior

If you are unsure where to put logic:

- shared model/runtime/export wiring -> top-level `agent/` or `generate/`
- catalog-level understanding -> `summarizer/`
- one-operation refinement -> `enhancer/`
- pipeline glue -> `orchestrator.py`
- FastMCP bootstrap/export -> `generate/`

## Scope and future AGENTS.md usage

Codex supports repository `AGENTS.md` files and applies them by directory-tree scope, with nearer files taking precedence over parent ones. In larger repos and monorepos, nested `AGENTS.md` files are a standard pattern for package-specific rules. citeturn539862search0turn539862search2turn539862search3

For now, keep this root `AGENTS.md` as the main source of truth.
If the repo grows substantially, add nested `AGENTS.md` files inside subpackages that truly need different rules.
