"""Shared builders for the sync_dotfiles test suite."""

from dataclasses import dataclass
from pathlib import Path

from sync_dotfiles import DotfilesSyncer, Manifest


@dataclass
class Env:
    """A fixture environment: a fake ``$HOME``, a repository, and a manifest."""

    home: Path
    dotfiles: Path
    config: Path
    manifest: Manifest


def write_tree(root: Path, files: dict[str, str]) -> None:
    """Write a mapping of relative paths to text contents under ``root``.

    Args:
        root: Directory to write into (created when missing).
        files: Mapping from POSIX-relative paths to file contents.
    """
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def build_env(
    tmp_path: Path,
    manifest_text: str,
    home_files: dict[str, str],
    repo_files: dict[str, str] | None = None,
) -> Env:
    """Build a fake home/repository/manifest environment.

    Args:
        tmp_path: Pytest temporary directory root.
        manifest_text: YAML manifest content.
        home_files: Files to create inside the fake ``$HOME``.
        repo_files: Files to create inside ``dotfiles/``.

    Returns:
        The assembled environment.
    """
    home = tmp_path / "home"
    repo = tmp_path / "repo"
    dotfiles = repo / "dotfiles"
    dotfiles.mkdir(parents=True)
    write_tree(home, home_files)
    write_tree(dotfiles, repo_files or {})

    config = repo / "dotfiles.yaml"
    config.write_text(manifest_text)
    return Env(
        home=home,
        dotfiles=dotfiles,
        config=config,
        manifest=Manifest.load(config),
    )


def make_syncer(env: Env, **kwargs: bool) -> DotfilesSyncer:
    """Create a ``DotfilesSyncer`` bound to a fixture environment.

    Args:
        env: The fixture environment.
        **kwargs: Forwarded as engine options (``dry_run``, ``prune``, ...).

    Returns:
        The engine instance.
    """
    return DotfilesSyncer(
        env.manifest,
        home_dir=env.home,
        dotfiles_dir=env.dotfiles,
        **kwargs,
    )


def snapshot(root: Path) -> dict[str, tuple[bytes, int, int]]:
    """Capture content, mode, and mtime of every regular file under ``root``.

    Args:
        root: Directory to snapshot.

    Returns:
        A mapping from POSIX-relative path to ``(content, mode, mtime_ns)``.
    """
    state = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        stat = path.stat()
        state[path.relative_to(root).as_posix()] = (
            path.read_bytes(),
            stat.st_mode & 0o7777,
            stat.st_mtime_ns,
        )
    return state


def managed_keys(syncer: DotfilesSyncer) -> list[str]:
    """Run a resolution and return the sorted managed home-relative paths.

    Args:
        syncer: The engine to resolve with.

    Returns:
        Sorted home-relative POSIX paths of managed files.
    """
    return sorted(syncer.assessment().managed)
