"""Cut a local tagged release after deterministic validation."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from oas2mcp._release import (
    VersionFiles,
    build_release_commit_message,
    build_release_tag,
    bump_version,
    find_unexpected_worktree_changes,
    read_current_version,
    write_release_version,
)


def build_parser() -> argparse.ArgumentParser:
    """Create the release-cut CLI parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Bump the repository version, refresh the lockfile, run release "
            "checks, then create a local Git commit and annotated tag."
        )
    )
    parser.add_argument(
        "--version",
        help="Explicit semantic version to cut, for example 0.1.8.",
    )
    parser.add_argument(
        "--part",
        choices=("major", "minor", "patch"),
        help="Version part to bump from the current package version.",
    )
    return parser


def run(
    args: list[str], *, cwd: Path, capture_output: bool = False
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with consistent error handling.

    Args:
        args: Command and arguments to execute.
        cwd: Working directory for the command.
        capture_output: Whether to capture stdout for later inspection.

    Returns:
        Completed subprocess result.
    """
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=capture_output,
    )


def ensure_clean_worktree(root: Path) -> None:
    """Fail when the repository already has unrelated local changes.

    Args:
        root: Repository root.

    Raises:
        SystemExit: If the worktree is not clean.
    """
    status = run(["git", "status", "--short"], cwd=root, capture_output=True).stdout
    unexpected = find_unexpected_worktree_changes(status, allowed_paths=set())
    if unexpected:
        joined = "\n".join(unexpected)
        raise SystemExit(
            "Refusing to cut a release with a dirty worktree.\n"
            f"Unexpected changes:\n{joined}"
        )


def ensure_tag_absent(root: Path, tag: str) -> None:
    """Fail when the target release tag already exists locally.

    Args:
        root: Repository root.
        tag: Annotated tag name to check.

    Raises:
        SystemExit: If the tag already exists.
    """
    existing = run(
        ["git", "tag", "-l", tag], cwd=root, capture_output=True
    ).stdout.strip()
    if existing:
        raise SystemExit(f"Git tag {tag} already exists.")


def main() -> int:
    """Run the local release-cut workflow."""
    parser = build_parser()
    parsed = parser.parse_args()

    if bool(parsed.version) == bool(parsed.part):
        parser.error("Provide exactly one of --version or --part.")

    root = Path(__file__).resolve().parents[1]
    files = VersionFiles(
        pyproject=root / "pyproject.toml",
        docs_conf=root / "docs/source/conf.py",
    )

    ensure_clean_worktree(root)

    current = read_current_version(files.pyproject)
    target = parsed.version or bump_version(current, parsed.part)
    if target == current:
        raise SystemExit(f"Version {target} is already current.")

    tag = build_release_tag(target)
    ensure_tag_absent(root, tag)

    write_release_version(target, files)
    run(["pdm", "lock"], cwd=root)
    run(["pdm", "run", "release_check"], cwd=root)

    tracked = ["pyproject.toml", "docs/source/conf.py", "pdm.lock"]
    run(["git", "add", *tracked], cwd=root)

    commit_message = build_release_commit_message(target)
    run(["git", "commit", "-m", commit_message], cwd=root)
    run(["git", "tag", "-a", tag, "-m", tag], cwd=root)

    print(f"Created local release commit and tag: {tag}")
    print("Next step: git push origin main && git push origin " + tag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
