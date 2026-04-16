Architecture
============

.. mermaid::

   flowchart LR
       A[OpenAPI spec] --> B[Parser]
       B --> C[Intermediate models]
       C --> D[MCP generation]
       D --> E[Python output]