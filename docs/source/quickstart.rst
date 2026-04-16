Quickstart
==========

Install
-------

.. code-block:: bash

   pdm install -G test -G docs

Environment
-----------

Copy the example env file and set the values you need:

.. code-block:: bash

   cp .env.example .env

Required for agent-driven summarizer and enhancer runs:

- ``OPENAI_API_KEY``

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

   pdm run python scripts/test_orchestrator.py
   pdm run python scripts/test_fastmcp_bootstrap.py
   pdm run python scripts/test_fastmcp_server.py
   pdm run python scripts/test_fastmcp_client.py
