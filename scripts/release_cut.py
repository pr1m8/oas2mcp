"""Cut a local tagged release after deterministic validation."""

from __future__ import annotations

import argparse
import os
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
    args: list[str],
    *,
    cwd: Path,
    capture_output: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with consistent error handling.

    Args:
        args: Command and arguments to execute.
        cwd: Working directory for the command.
        capture_output: Whether to capture stdout for later inspection.
        env: Optional environment overrides.

    Returns:
        Completed subprocess result.
    """
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=capture_output,
        env=env,
    )


def build_command_env(root: Path) -> dict[str, str]:
    """Build subprocess environment with repo-local PDM logging.

    Args:
        root: Repository root.

    Returns:
        Environment variables for subprocess calls.
    """
    env = os.environ.copy()
    pdm_log_dir = root / ".pdm-logs"
    uv_cache_dir = root / ".uv-cache"
    pdm_log_dir.mkdir(exist_ok=True)
    uv_cache_dir.mkdir(exist_ok=True)
    env.setdefault("PDM_LOG_DIR", str(pdm_log_dir))
    env.setdefault("UV_CACHE_DIR", str(uv_cache_dir))
    return env


def snapshot_release_files(root: Path, tracked: list[str]) -> dict[str, str]:
    """Snapshot tracked release files before mutating them.

    Args:
        root: Repository root.
        tracked: Repository-relative tracked files to restore.

    Returns:
        Original file contents keyed by repository-relative path.
    """
    return {
        path: (root / path).read_text(encoding="utf-8")
        for path in tracked
        if (root / path).exists()
    }


def restore_release_files(root: Path, originals: dict[str, str]) -> None:
    """Restore tracked release files after a failed release cut.

    Args:
        root: Repository root.
        originals: Original file contents keyed by repository-relative path.
    """
    for path, contents in originals.items():
        (root / path).write_text(contents, encoding="utf-8")


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
    env = build_command_env(root)

    ensure_clean_worktree(root)

    current = read_current_version(files.pyproject)
    target = parsed.version or bump_version(current, parsed.part)
    if target == current:
        raise SystemExit(f"Version {target} is already current.")

    tag = build_release_tag(target)
    ensure_tag_absent(root, tag)

    tracked = ["pyproject.toml", "docs/source/conf.py", "pdm.lock"]
    originals = snapshot_release_files(root, tracked)
    committed = False
    try:
        write_release_version(target, files)
        run(["pdm", "lock"], cwd=root, env=env)
        run(["pdm", "run", "release_check"], cwd=root, env=env)

        run(["git", "add", *tracked], cwd=root)

        commit_message = build_release_commit_message(target)
        run(["git", "commit", "-m", commit_message], cwd=root)
        committed = True
        run(["git", "tag", "-a", tag, "-m", tag], cwd=root)
    except subprocess.CalledProcessError as exc:
        if not committed:
            restore_release_files(root, originals)
        raise SystemExit(exc.returncode) from exc

    print(f"Created local release commit and tag: {tag}")
    print("Next step: git push origin main && git push origin " + tag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
