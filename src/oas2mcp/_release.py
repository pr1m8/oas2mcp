"""Release automation helpers for repository version files.

This module keeps version bump logic deterministic and easy to test.
It intentionally updates only the small set of source-controlled files that
carry release metadata for this project.
"""

from __future__ import annotations

import re
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path

VERSION_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


@dataclass(frozen=True)
class VersionFiles:
    """Repository files that store the current release version."""

    pyproject: Path
    docs_conf: Path


def build_release_tag(version: str) -> str:
    """Build the annotated Git tag name for a release.

    Args:
        version: Semantic version in ``X.Y.Z`` form.

    Returns:
        Git tag name in ``vX.Y.Z`` form.
    """
    parse_version(version)
    return f"v{version}"


def build_release_commit_message(version: str) -> str:
    """Build the release commit message for a version.

    Args:
        version: Semantic version in ``X.Y.Z`` form.

    Returns:
        Commit message in ``Release vX.Y.Z`` form.
    """
    return f"Release {build_release_tag(version)}"


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse a semantic version string.

    Args:
        version: Semantic version in ``X.Y.Z`` form.

    Returns:
        Parsed major, minor, and patch integers.

    Raises:
        ValueError: If the version does not match ``X.Y.Z``.
    """
    match = VERSION_PATTERN.match(version)
    if not match:
        raise ValueError(f"Invalid version '{version}'. Expected X.Y.Z.")
    return tuple(int(part) for part in match.groups())


def bump_version(version: str, part: str) -> str:
    """Increment a semantic version string by one part.

    Args:
        version: Current semantic version.
        part: Which part to bump: ``major``, ``minor``, or ``patch``.

    Returns:
        The incremented semantic version string.

    Raises:
        ValueError: If ``part`` is unsupported.
    """
    major, minor, patch = parse_version(version)

    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"

    raise ValueError(f"Unsupported bump part '{part}'.")


def read_current_version(pyproject_path: Path) -> str:
    """Read the current package version from ``pyproject.toml``.

    Args:
        pyproject_path: Path to the project metadata file.

    Returns:
        Current semantic version string.

    Raises:
        ValueError: If the version line cannot be found.
    """
    text = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', text, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"Could not find version in {pyproject_path}.")
    return match.group(1)


def apply_version_update(
    text: str, pattern: str, replacement: str, *, path: Path
) -> str:
    """Update a single version-bearing line in text.

    Args:
        text: File contents to modify.
        pattern: Regex pattern for the current version-bearing line.
        replacement: Replacement line.
        path: Path used in error messages.

    Returns:
        Updated text.

    Raises:
        ValueError: If the pattern is not found exactly once.
    """
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(
            f"Expected to update one version line in {path}, updated {count}."
        )
    return updated


def write_release_version(version: str, files: VersionFiles) -> None:
    """Write the release version into tracked source files.

    Args:
        version: New semantic version string.
        files: Target file bundle.
    """
    parse_version(version)

    pyproject_text = files.pyproject.read_text(encoding="utf-8")
    pyproject_updated = apply_version_update(
        pyproject_text,
        r'^version = "[^"]+"$',
        f'version = "{version}"',
        path=files.pyproject,
    )
    files.pyproject.write_text(pyproject_updated, encoding="utf-8")

    docs_conf_text = files.docs_conf.read_text(encoding="utf-8")
    docs_conf_updated = apply_version_update(
        docs_conf_text,
        r'^release = "[^"]+"$',
        f'release = "{version}"',
        path=files.docs_conf,
    )
    files.docs_conf.write_text(docs_conf_updated, encoding="utf-8")


def find_unexpected_worktree_changes(
    status_output: str, allowed_paths: Collection[str]
) -> list[str]:
    """Return Git status entries that fall outside an allowed path set.

    Args:
        status_output: Raw ``git status --short`` output.
        allowed_paths: Repository-relative paths that may be modified.

    Returns:
        Unexpected non-empty status lines.
    """
    unexpected: list[str] = []
    for line in status_output.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if path not in allowed_paths:
            unexpected.append(line.strip())
    return unexpected
