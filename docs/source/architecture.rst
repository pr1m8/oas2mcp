Architecture
============

.. mermaid::

   flowchart LR
       A[OpenAPI spec] --> B[Loader]
       B --> C[Normalization]
       C --> D[Deterministic classification]
       D --> E[Catalog summarizer]
       E --> F[Operation enhancer]
       F --> G[Catalog surface planner]
       G --> H[Enhanced catalog export]
       H --> I[FastMCP bootstrap or LangGraph deployment]

Pipeline responsibilities
-------------------------

- ``loaders/`` fetches and parses OpenAPI sources.
- ``normalize/`` converts raw documents into stable internal models.
- ``classify/`` produces deterministic MCP hints.
- ``agent/summarizer/`` understands the API at the catalog level.
- ``agent/enhancer/`` refines one operation at a time.
- ``agent/surface/`` plans the shared MCP surface.
- ``generate/`` exports artifacts and bootstraps FastMCP.
- ``deploy/`` exposes LangGraph deployment wrappers around the orchestrator.

Design principles
-----------------

- Prefer deterministic transforms before agentic behavior.
- Treat classification outputs as hints, not final truth.
- Preserve provenance back to ``operationId`` and ``METHOD path``.
- Keep orchestration reliable and mostly deterministic.
- Keep root-level generated artifacts opt-in; prefer dedicated export and config directories.
