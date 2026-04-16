Architecture
============

.. mermaid::

   flowchart LR
       A[OpenAPI spec] --> B[Loader]
       B --> C[Normalization]
       C --> D[Deterministic classification]
       D --> E[Catalog summarizer]
       E --> F[Operation enhancer]
       F --> G[Enhanced catalog export]
       G --> H[FastMCP bootstrap]

Pipeline responsibilities
-------------------------

- ``loaders/`` fetches and parses OpenAPI sources.
- ``normalize/`` converts raw documents into stable internal models.
- ``classify/`` produces deterministic MCP hints.
- ``agent/summarizer/`` understands the API at the catalog level.
- ``agent/enhancer/`` refines one operation at a time.
- ``generate/`` exports artifacts and bootstraps FastMCP.

Design principles
-----------------

- Prefer deterministic transforms before agentic behavior.
- Treat classification outputs as hints, not final truth.
- Preserve provenance back to ``operationId`` and ``METHOD path``.
- Keep orchestration reliable and mostly deterministic.
