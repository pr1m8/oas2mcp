"""Tests for release automation helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from oas2mcp._release import (
    VersionFiles,
    build_release_commit_message,
    build_release_tag,
    bump_version,
    find_unexpected_worktree_changes,
    parse_version,
    read_current_version,
    write_release_version,
)


def test_parse_version_rejects_invalid_strings() -> None:
    """Release parsing should reject non-semver values."""
    with pytest.raises(ValueError):
        parse_version("1.2")


def test_bump_version_updates_requested_part() -> None:
    """Version bumps should reset lower-order parts appropriately."""
    assert bump_version("0.1.4", "patch") == "0.1.5"
    assert bump_version("0.1.4", "minor") == "0.2.0"
    assert bump_version("0.1.4", "major") == "1.0.0"


def test_release_git_metadata_is_derived_from_version() -> None:
    """Release commit and tag names should stay in sync with the version."""
    assert build_release_tag("0.1.8") == "v0.1.8"
    assert build_release_commit_message("0.1.8") == "Release v0.1.8"


def test_find_unexpected_worktree_changes_filters_allowed_paths() -> None:
    """Only unrelated worktree changes should block the release helper."""
    status = " M pyproject.toml\n M docs/source/conf.py\n?? README.md\n"
    unexpected = find_unexpected_worktree_changes(
        status,
        allowed_paths={"pyproject.toml", "docs/source/conf.py"},
    )

    assert unexpected == ["?? README.md"]


def test_write_release_version_updates_tracked_files(tmp_path: Path) -> None:
    """Release file updates should touch package and docs metadata together."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('version = "0.1.4"\n', encoding="utf-8")

    docs_conf = tmp_path / "conf.py"
    docs_conf.write_text('release = "0.1.4"\n', encoding="utf-8")

    files = VersionFiles(pyproject=pyproject, docs_conf=docs_conf)

    assert read_current_version(pyproject) == "0.1.4"

    write_release_version("0.1.5", files)

    assert 'version = "0.1.5"' in pyproject.read_text(encoding="utf-8")
    assert 'release = "0.1.5"' in docs_conf.read_text(encoding="utf-8")
