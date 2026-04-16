"""Export configuration models for ``oas2mcp`` generation."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field

from oas2mcp.models.normalized import NormalizedBaseModel


class ExportConfig(NormalizedBaseModel):
    """Configuration for enhanced artifact export.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.

    Examples:
        .. code-block:: python

            config = ExportConfig(
                project_root=Path.cwd(),
                export_dir="data/exports",
                write_root_snapshot=True,
            )
    """

    project_root: Path = Field(default_factory=Path.cwd)
    export_dir: str = "data/exports"

    write_root_snapshot: bool = True
    root_snapshot_name: str | None = None

    write_operation_notes: bool = True
    write_fastmcp_config: bool = True

    @property
    def resolved_export_dir(self) -> Path:
        """Return the resolved export directory.

        Args:
            None.

        Returns:
            Path: The resolved export directory path.

        Raises:
            None.
        """
        return self.project_root / self.export_dir
