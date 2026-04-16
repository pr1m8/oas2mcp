Examples
========

Pytest
------

Run the formal test suite:

.. code-block:: bash

   pdm run pytest

FastMCP bootstrap
-----------------

Generate artifacts and inspect the bootstrap path manually:

.. code-block:: bash

   pdm run python scripts/test_orchestrator.py
   pdm run python scripts/test_fastmcp_bootstrap.py
   pdm run python scripts/test_fastmcp_server.py
   pdm run python scripts/test_fastmcp_client.py

The server and client scripts are intended for local inspection after the formal
pytest suite has already passed.

Generated artifacts
-------------------

Typical outputs land in ``data/exports/``:

- ``<catalog-slug>_enhanced_catalog.json``
- ``<catalog-slug>_operation_notes.json``
- ``<catalog-slug>_fastmcp_config.json``

These artifacts are intentionally human-inspectable and useful for debugging export and bootstrap changes.
