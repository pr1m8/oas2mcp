"""Update repository version files for a release."""

from __future__ import annotations

import argparse
from pathlib import Path

from oas2mcp._release import (
    VersionFiles,
    bump_version,
    read_current_version,
    write_release_version,
)


def build_parser() -> argparse.ArgumentParser:
    """Create the release-version CLI parser."""
    parser = argparse.ArgumentParser(
        description="Update repository versioned files for a release."
    )
    parser.add_argument(
        "--version",
        help="Explicit semantic version to write, for example 0.1.4.",
    )
    parser.add_argument(
        "--part",
        choices=("major", "minor", "patch"),
        help="Version part to bump from the current package version.",
    )
    return parser


def main() -> int:
    """Run the version update script."""
    parser = build_parser()
    args = parser.parse_args()

    if bool(args.version) == bool(args.part):
        parser.error("Provide exactly one of --version or --part.")

    root = Path(__file__).resolve().parents[1]
    files = VersionFiles(
        pyproject=root / "pyproject.toml",
        docs_conf=root / "docs/source/conf.py",
    )

    current = read_current_version(files.pyproject)
    target = args.version or bump_version(current, args.part)

    write_release_version(target, files)
    print(f"Updated release version: {current} -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
