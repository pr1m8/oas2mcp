Quickstart
==========

Install
-------

.. code-block:: bash

   pdm install -G test -G docs -G cli

The ``cli`` group includes the in-memory LangGraph API server extras required
for ``langgraph dev``.

Environment
-----------

Copy the example env file and set the values you need:

.. code-block:: bash

   cp .env.example .env

Required for the agent pipeline:

- ``OPENAI_API_KEY``

Optional for LangSmith tracing and LangGraph deployment:

- ``LANGSMITH_TRACING=true``
- ``LANGSMITH_API_KEY``
- ``LANGSMITH_PROJECT``
- ``LANGSMITH_WORKSPACE_ID``
- ``LANGSMITH_DEPLOYMENT_NAME``
- ``LANGSMITH_ENDPOINT`` for self-hosted LangSmith only

Optional for live upstream FastMCP calls:

- ``UPSTREAM_BEARER_TOKEN``
- ``UPSTREAM_API_KEY``
- ``UPSTREAM_API_KEY_HEADER``

Test
----

.. code-block:: bash

   pdm run pytest

Manual smoke checks
-------------------

Formal coverage now lives in ``tests/``. The scripts remain available for interactive inspection:

.. code-block:: bash

   pdm run python scripts/test_catalog_surface_planner_agent.py
   pdm run python scripts/test_orchestrator.py
   pdm run python scripts/test_fastmcp_bootstrap.py
   pdm run python scripts/test_fastmcp_server.py
   pdm run python scripts/test_fastmcp_client.py

LangGraph deployment
--------------------

The repository includes deployable graph entrypoints in
``src/oas2mcp/deploy/langgraph_app.py`` and a deployment config at
``config/langgraph.json``.

Run the LangGraph CLI commands from the repository root so the config's
``./src`` and ``./.env`` paths resolve correctly.

Install the CLI group:

.. code-block:: bash

   pdm install -G cli

Run the LangGraph dev server locally:

.. code-block:: bash

   pdm run langgraph dev --config config/langgraph.json --no-browser

The configured graphs are:

- ``enhance_catalog`` for the in-memory summarize/enhance/surface-planning pipeline
- ``enhance_and_export_catalog`` for the export pipeline that returns written artifact paths

Validate the deployment config:

.. code-block:: bash

   pdm run langgraph validate --config config/langgraph.json

Build or deploy with the LangGraph CLI:

.. code-block:: bash

   pdm run langgraph build --config config/langgraph.json -t oas2mcp
   pdm run langgraph deploy --config config/langgraph.json
