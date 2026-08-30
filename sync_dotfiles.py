#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["pyyaml"]
# ///
"""Sync dotfiles from the user's home directory into the repository.

The sync is driven by a YAML manifest (``dotfiles.yaml`` by default) built
from a single recursive grammar: every scope, from ``$HOME`` down to
individual directories, uses the same ``include:``/``exclude:`` lists. The
script reports changes after syncing but never commits or pushes; see
``--help`` for the available modes.
"""

import argparse
import filecmp
import fnmatch
import logging
import re
import shutil
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal

import yaml

REPO_DIR = Path(__file__).parent.resolve()
DOTFILES_DIR = REPO_DIR / "dotfiles"
DEFAULT_CONFIG_PATH = REPO_DIR / "dotfiles.yaml"
HOME_DIR = Path.home()

logger = logging.getLogger("sync_dotfiles")

_ROOT_KEYS = frozenset({"include", "exclude", "secret_patterns"})
_SCOPE_KEYS = frozenset({"include", "exclude"})
_INCLUDE_ITEM_KEYS = frozenset({"path", "optional", "include", "exclude"})
_EXCLUDE_ITEM_KEYS = frozenset({"pattern", "optional", "allow_orphan"})
_GLOB_CHARS = re.compile(r"[*?\[]")
PathParts = tuple[str, ...]


class ConfigError(Exception):
    """Raised when the manifest is missing, unparsable, or invalid."""


class SecretGuard:
    """Scan outgoing files for well-known secret signatures."""

    _BUILT_INS = (
        ("private key block", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
        ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
        (
            "credential assignment",
            re.compile(
                r"\b(api[_-]?key|secret|secret[_-]?key|token|password|passwd)"
                r"\s*[=:]\s*['\"](?!\$)[^'\"]{8,}['\"]",
                re.IGNORECASE,
            ),
        ),
        (
            "credential assignment",
            re.compile(
                r"\b(api[_-]?key|secret|secret[_-]?key|token|password|passwd)"
                r"\s*[=:]\s*[A-Za-z0-9+/_\-]{20,}",
                re.IGNORECASE,
            ),
        ),
    )

    def __init__(self, extra_patterns: tuple[re.Pattern[str], ...]):
        """Initialize ``SecretGuard``.

        Args:
            extra_patterns: Manifest-defined ``secret_patterns`` beyond the
                built-in signatures.
        """
        self._patterns = (
            *self._BUILT_INS,
            *(("manifest pattern", pattern) for pattern in extra_patterns),
        )

    def scan(self, path: Path) -> list[str]:
        """Return the names of signatures found in a file.

        Args:
            path: The file to scan.

        Returns:
            Signature descriptions; ``["unreadable"]`` when the file cannot be
                read at all, and empty when the file is clean or unreadable as
                text (binary content carries no text signatures).
        """
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.debug(f"{path}: not readable as text; no secret signatures found")
            return []
        except OSError as error:
            logger.debug(f"{path}: cannot read file for secret scan: {error}")
            return ["unreadable"]
        findings = []
        for name, pattern in self._patterns:
            if pattern.search(text):
                findings.append(name)
        # the built-in quoted and unquoted credential rules share a name
        return list(dict.fromkeys(findings))


@dataclass(frozen=True, eq=False)
class Exclude:
    """A regex prune rule within a scope.

    Attributes:
        pattern: Compiled regex applied with search semantics to paths relative
            to the scope the pattern was declared in.
        source: Raw pattern text, used in messages.
        optional: Whether the pattern is allowed to match nothing.
        allow_orphan: Whether repository files beneath matching paths are
            tolerated: reported neither as orphans nor deleted by ``--prune``
            (the ``$HOME`` side stays untracked either way).

    Identity equality keeps usage counts per declaration: with Python 3.14's
    value equality for compiled patterns, two scopes declaring the same regex
    would otherwise share one count and mask each other's unused-pattern lint.
    """

    pattern: re.Pattern[str]
    source: str
    optional: bool
    allow_orphan: bool


ExcludeChain = tuple[tuple[PathParts, tuple[Exclude, ...]], ...]


@dataclass(frozen=True)
class Include:
    """An include item: a literal path or glob, optionally with a nested scope.

    Attributes:
        path: POSIX path or glob relative to the enclosing scope's base.
        parts: Path components of ``path`` (glob metacharacters preserved).
        glob: Whether ``path`` contains glob metacharacters.
        optional: Whether the entry may be missing in ``$HOME`` without a
            warning and without being pruned from the repository.
        scope: Nested scope for directory entries; its lists are relative to
            the directory this item points at.
    """

    path: str
    parts: PathParts
    glob: bool
    optional: bool
    scope: "Scope | None"


@dataclass(frozen=True)
class Scope:
    """A selection scope: include/exclude lists relative to a base directory.

    Attributes:
        include: Items selecting paths within the scope's base directory.
        exclude: Patterns pruning selected paths within the scope's base.
    """

    include: tuple[Include, ...]
    exclude: tuple[Exclude, ...]


@dataclass(frozen=True)
class Manifest:
    """Parsed manifest: the root scope (``$HOME``) plus secret patterns.

    Attributes:
        root: Root scope whose include/exclude lists are ``$HOME``-relative.
        secret_patterns: Extra regexes for the secret guard, beyond built-ins.
        path: Path the manifest was loaded from, used in messages.
    """

    root: Scope
    secret_patterns: tuple[re.Pattern[str], ...]
    path: Path

    @classmethod
    def load(cls, path: Path) -> "Manifest":
        """Load, parse, and validate the manifest at ``path``.

        Args:
            path: Path to the YAML manifest.

        Returns:
            The parsed manifest.

        Raises:
            ConfigError: If the file cannot be read, is not valid YAML, or
                violates the manifest schema.
        """
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            raise ConfigError(f"{path}: YAML parse error: {error}") from error
        except OSError as error:
            raise ConfigError(f"{path}: cannot read manifest: {error}") from error

        if raw is None:
            raise ConfigError(f"{path}: manifest is empty")
        if not isinstance(raw, dict):
            raise ConfigError(f"{path}: manifest must be a mapping at the top level")

        root = _parse_scope(
            raw,
            location=path.name,
            base=(),
            is_root=True,
            chain=(),
        )
        secret_patterns = _parse_secret_patterns(
            raw.get("secret_patterns"),
            location=path.name,
        )
        return cls(root=root, secret_patterns=secret_patterns, path=path)


def _parse_scope(
    data: dict,
    location: str,
    base: PathParts,
    is_root: bool,
    chain: ExcludeChain,
) -> Scope:
    """Parse one scope (the root scope or a nested directory scope).

    Args:
        data: Raw mapping holding ``include:``/``exclude:`` lists.
        location: Human-readable location for error messages.
        base: Home-relative directory components the scope's lists are
            relative to.
        is_root: Whether this is the root scope.
        chain: ``(base, excludes)`` for each ancestor scope, root first.

    Returns:
        The parsed scope.

    Raises:
        ConfigError: On unknown keys, missing/empty lists, or invalid items.
    """
    if not isinstance(data, dict):
        raise ConfigError(f"{location}: scope must be a mapping")

    allowed_keys = _ROOT_KEYS if is_root else _SCOPE_KEYS
    unknown_keys = sorted(set(data) - allowed_keys)
    if unknown_keys:
        raise ConfigError(
            f"{location}: unknown key(s) {', '.join(map(repr, unknown_keys))}; "
            f"expected only {', '.join(sorted(allowed_keys))}"
        )

    include_data = data.get("include")
    if is_root and include_data is None:
        raise ConfigError(f"{location}: missing required 'include' list")
    if include_data is not None and not isinstance(include_data, list):
        raise ConfigError(f"{location}: 'include' must be a list")
    if include_data is not None and not include_data:
        raise ConfigError(
            f"{location}: 'include' must not be empty; "
            "omit the key to select the whole directory"
        )

    exclude_data = data.get("exclude")
    if exclude_data is not None:
        if not isinstance(exclude_data, list):
            raise ConfigError(f"{location}: 'exclude' must be a list")
        if not exclude_data:
            raise ConfigError(
                f"{location}: 'exclude' must not be empty; omit it instead"
            )

    # excludes are parsed first so include items can be validated against them
    excludes = tuple(
        _parse_exclude_item(item, f"{location}.exclude[{index}]")
        for index, item in enumerate(exclude_data or [])
    )
    full_chain = (*chain, (base, excludes))
    includes = tuple(
        _parse_include_item(
            item,
            location=f"{location}.include[{index}]",
            base=base,
            chain=full_chain,
        )
        for index, item in enumerate(include_data or [])
    )
    return Scope(include=includes, exclude=excludes)


def _parse_include_item(
    item: str | dict,
    location: str,
    base: PathParts,
    chain: ExcludeChain,
) -> Include:
    """Parse a single include item and validate it against enclosing excludes.

    Args:
        item: Raw item: a plain string or a mapping with ``path:``.
        location: Human-readable location for error messages.
        base: Home-relative directory components the item's path is relative to.
        chain: ``(base, excludes)`` for the enclosing scope and all of its
            ancestors, used for load-time include-under-exclude checks.

    Returns:
        The parsed include item.

    Raises:
        ConfigError: On invalid items or paths escaping/excluded in ``$HOME``.
    """
    if isinstance(item, str):
        path, optional, nested_data = item, False, None
    elif isinstance(item, dict):
        unknown_keys = sorted(set(item) - _INCLUDE_ITEM_KEYS)
        if unknown_keys:
            raise ConfigError(
                f"{location}: unknown key(s) {', '.join(map(repr, unknown_keys))}; "
                f"expected only {', '.join(sorted(_INCLUDE_ITEM_KEYS))}"
            )
        if "path" not in item:
            raise ConfigError(f"{location}: mapping include items require a 'path' key")
        path = item["path"]
        if not isinstance(path, str) or not path:
            raise ConfigError(f"{location}: 'path' must be a non-empty string")
        optional = _parse_bool(item.get("optional", False), "optional", location)
        nested_data = {
            key: item[key] for key in ("include", "exclude") if key in item
        } or None
    else:
        raise ConfigError(f"{location}: include items must be strings or mappings")

    parts = _validate_item_path(path, location)
    is_glob = bool(_GLOB_CHARS.search(path))
    if is_glob and nested_data is not None:
        raise ConfigError(
            f"{location}: glob include items cannot carry a nested "
            "include/exclude scope; nest the scope under a literal path"
        )

    _check_include_against_excludes(
        parts=parts, base=base, chain=chain, location=location, is_glob=is_glob
    )

    nested_scope = None
    if nested_data is not None:
        nested_scope = _parse_scope(
            nested_data,
            location=location,
            base=base + parts,
            is_root=False,
            chain=chain,
        )
    return Include(
        path=path, parts=parts, glob=is_glob, optional=optional, scope=nested_scope
    )


def _parse_exclude_item(item: str | dict, location: str) -> Exclude:
    """Parse a single exclude item.

    Args:
        item: Raw item: a plain regex string or a mapping with ``pattern:``.
        location: Human-readable location for error messages.

    Returns:
        The parsed exclude item.

    Raises:
        ConfigError: On invalid items or regexes.
    """
    if isinstance(item, str):
        source, optional, allow_orphan = item, False, False
    elif isinstance(item, dict):
        unknown_keys = sorted(set(item) - _EXCLUDE_ITEM_KEYS)
        if unknown_keys:
            raise ConfigError(
                f"{location}: unknown key(s) {', '.join(map(repr, unknown_keys))}; "
                f"expected only {', '.join(sorted(_EXCLUDE_ITEM_KEYS))}"
            )
        if "pattern" not in item:
            raise ConfigError(
                f"{location}: mapping exclude items require a 'pattern' key"
            )
        source = item["pattern"]
        if not isinstance(source, str) or not source:
            raise ConfigError(f"{location}: 'pattern' must be a non-empty string")
        optional = _parse_bool(item.get("optional", False), "optional", location)
        allow_orphan = _parse_bool(
            item.get("allow_orphan", False), "allow_orphan", location
        )
    else:
        raise ConfigError(f"{location}: exclude items must be strings or mappings")

    try:
        pattern = re.compile(source)
    except re.error as error:
        raise ConfigError(f"{location}: invalid regex {source!r}: {error}") from error
    return Exclude(
        pattern=pattern, source=source, optional=optional, allow_orphan=allow_orphan
    )


def _parse_secret_patterns(
    data: list | None, location: str
) -> tuple[re.Pattern[str], ...]:
    """Parse the manifest's extra secret-guard patterns.

    Args:
        data: Raw list of regex strings, or None when absent.
        location: Human-readable location for error messages.

    Returns:
        The compiled secret patterns (empty when absent).

    Raises:
        ConfigError: On invalid entries or regexes.
    """
    if data is None:
        return ()
    if not isinstance(data, list):
        raise ConfigError(f"{location}: 'secret_patterns' must be a list")
    patterns: list[re.Pattern[str]] = []
    for index, item in enumerate(data):
        if not isinstance(item, str) or not item:
            raise ConfigError(
                f"{location}.secret_patterns[{index}]: must be a non-empty regex string"
            )
        try:
            patterns.append(re.compile(item))
        except re.error as error:
            raise ConfigError(
                f"{location}.secret_patterns[{index}]: invalid regex {item!r}: {error}"
            ) from error
    return tuple(patterns)


def _parse_bool(value: object, key: str, location: str) -> bool:
    """Validate and return a boolean manifest flag value.

    Args:
        value: Raw value of the flag key.
        key: Name of the flag key, used in error messages.
        location: Human-readable location for error messages.

    Returns:
        The flag as a bool.

    Raises:
        ConfigError: If the value is not a bool.
    """
    if not isinstance(value, bool):
        raise ConfigError(f"{location}: '{key}' must be a boolean")
    return value


def _validate_item_path(path: str, location: str) -> PathParts:
    """Validate that an item path is relative and stays within its scope.

    Args:
        path: The raw path or glob string.
        location: Human-readable location for error messages.

    Returns:
        The validated path components.

    Raises:
        ConfigError: If the path is absolute, empty, or contains ``..``.
    """
    pure_path = PurePosixPath(path)
    if pure_path.is_absolute() or path.startswith("/"):
        raise ConfigError(f"{location}: path {path!r} must be relative")
    if not path.strip():
        raise ConfigError(f"{location}: path must be a non-empty string")
    if ".." in pure_path.parts:
        raise ConfigError(f"{location}: path {path!r} must not contain '..'")
    # "." selects the scope's own directory (whole-home include at the root)
    return pure_path.parts


def _check_include_against_excludes(
    parts: PathParts,
    base: PathParts,
    chain: ExcludeChain,
    location: str,
    is_glob: bool,
) -> None:
    """Reject include items that directly match or sit beneath an exclude.

    Literal items are rejected when the item path itself matches an exclude of
    its own or an ancestor scope. Both literal and glob items are rejected when
    a fixed ancestor directory of the item is excluded, since the item could
    then only ever select pruned paths.

    Args:
        parts: The item's validated path components, relative to ``base``.
        base: Home-relative directory components the item's path is relative to.
        chain: ``(base, excludes)`` for the item's scope and its ancestors.
        location: Human-readable location for error messages.
        is_glob: Whether the item's path contains glob metacharacters.

    Raises:
        ConfigError: If the item matches, or is nested beneath, an exclude
            pattern.
    """
    home_relative = base + parts
    for scope_base, excludes in chain:
        relative = home_relative[len(scope_base) :]
        for exclude in excludes:
            if not is_glob and exclude.pattern.search("/".join(relative)):
                raise ConfigError(
                    f"{location}: include item {'/'.join(home_relative)!r} is excluded "
                    f"by pattern {exclude.source!r}"
                )
            for depth in range(1, len(relative)):
                ancestor = "/".join(relative[:depth])
                if exclude.pattern.search(ancestor):
                    raise ConfigError(
                        f"{location}: include item {'/'.join(home_relative)!r} is nested "
                        f"beneath excluded path {ancestor!r} (pattern {exclude.source!r})"
                    )


def _configure_logging(verbose: bool, quiet: bool) -> None:
    """Configure root logging once.

    Args:
        verbose: Enable debug logging.
        quiet: Restrict logging to warnings and errors.
    """
    level = logging.DEBUG if verbose else logging.WARNING if quiet else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(levelname)s %(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@dataclass(frozen=True)
class ManagedFile:
    """A file in ``$HOME`` covered by the manifest, awaiting sync.

    Attributes:
        rel: Home-relative POSIX path of the file.
        source: Absolute path to read the content from (the resolved target for
            followed symlinks, otherwise the path inside ``$HOME`` itself).
    """

    rel: PurePosixPath
    source: Path


@dataclass(frozen=True)
class MissingEntry:
    """A literal manifest entry whose path does not exist in ``$HOME``.

    Attributes:
        rel: Home-relative POSIX path of the missing entry.
        optional: Whether the entry is exempt from warnings and pruning.
    """

    rel: PurePosixPath
    optional: bool


@dataclass(frozen=True)
class MissingCopy:
    """A repository copy of a manifest entry that is missing in ``$HOME``.

    Attributes:
        rel: Repository-relative POSIX path of the copy.
        optional: Whether the owning entry is exempt from pruning.
    """

    rel: PurePosixPath
    optional: bool


@dataclass(frozen=True)
class WatchCandidate:
    """An untracked ``$HOME`` path surfaced by the untracked watch.

    Attributes:
        rel: Home-relative POSIX path of the candidate.
        scope: ``home`` for top-level dot-entries, otherwise the home-relative
            path of the curated directory the candidate was found in.
    """

    rel: PurePosixPath
    scope: str


@dataclass(frozen=True)
class EntryRecord:
    """Bookkeeping for a literal include entry, for repository classification.

    Attributes:
        parts: Home-relative path components of the entry.
        abs: Absolute path of the entry in ``$HOME`` (resolved for followed
            symlinks).
        kind: ``dir`` for directory entries, ``file`` for file entries, and
            ``missing`` for entries absent from ``$HOME``.
        scope: The entry's nested scope, if any.
        chain: Exclude scopes ``(base, excludes)`` enclosing the entry.
    """

    parts: PathParts
    abs: Path
    kind: Literal["dir", "file", "missing"]
    scope: Scope | None
    chain: ExcludeChain


@dataclass
class Assessment:
    """Everything one resolution pass learned about ``$HOME`` and the repo.

    Attributes:
        managed: Files present in ``$HOME`` and covered by the manifest, keyed
            by home-relative POSIX path.
        missing_entries: Literal entries absent from ``$HOME`` (including
            ``optional`` ones, which reporting filters out).
        stale: Repository files covered by a live directory entry but missing
            in ``$HOME``; synced runs mirror-delete them.
        missing_copies: Repository copies of entries missing in ``$HOME``;
            only ``--prune`` removes them, and never ``optional`` ones.
        skipped_copies: Repository files whose ``$HOME`` counterpart is an
            unfollowed symlink; reported but never deleted.
        orphans: Repository files not covered by the manifest at all.
        allowed_orphans: Repository files beneath ``allow_orphan`` excludes;
            tolerated — never warned about and never pruned.
        watch: Untracked candidates from both watch scopes.
        symlink_skips: Symlinks skipped because ``--follow-symlinks`` is off.
        errors: Broken symlinks, type mismatches, and execution failures.
        pattern_uses: How often each exclude pattern matched anything.
    """

    managed: dict[str, ManagedFile]
    missing_entries: tuple[MissingEntry, ...]
    stale: tuple[PurePosixPath, ...]
    missing_copies: tuple[MissingCopy, ...]
    skipped_copies: tuple[PurePosixPath, ...]
    orphans: tuple[PurePosixPath, ...]
    allowed_orphans: tuple[PurePosixPath, ...]
    watch: tuple[WatchCandidate, ...]
    symlink_skips: tuple[PurePosixPath, ...]
    errors: tuple[str, ...]
    pattern_uses: dict[Exclude, int]


@dataclass(frozen=True)
class FileAction:
    """A planned copy of a managed file into the repository.

    Attributes:
        rel: Home-relative POSIX path of the file.
        source: Absolute path to read the content from (the resolved target for
            followed symlinks, otherwise the path inside ``$HOME`` itself).
        action: ``add`` for new repository files, ``modify`` for changed ones.
    """

    rel: PurePosixPath
    source: Path
    action: Literal["add", "modify"]


@dataclass(frozen=True)
class DeleteAction:
    """A planned repository-side deletion.

    Attributes:
        rel: Repository-relative POSIX path of the file.
        reason: ``delete`` for deletions mirrored from ``$HOME``, or
            ``prune-orphan``/``prune-missing`` for ``--prune`` deletions.
    """

    rel: PurePosixPath
    reason: Literal["delete", "prune-orphan", "prune-missing"]


@dataclass
class SyncPlan:
    """The full set of changes a sync run would apply.

    Attributes:
        copies: Files to copy into the repository.
        mirror_deletes: Repository files to delete because they vanished from
            a live directory entry in ``$HOME``.
        prune_deletes: Repository files ``--prune`` would remove.
        skipped_secrets: Files the secret guard refused to copy (warning only
            unless ``--strict-secrets`` aborted the run).
        aborted: Whether ``--strict-secrets`` aborted the run before any
            change was applied.
        errors: Plan-time failures (repository-symlink clashes, comparison
            errors, unreadable files, strict-secret aborts).
    """

    copies: tuple[FileAction, ...]
    mirror_deletes: tuple[DeleteAction, ...]
    prune_deletes: tuple[DeleteAction, ...]
    skipped_secrets: tuple[PurePosixPath, ...]
    aborted: bool
    errors: tuple[str, ...]


def _watch_scope_label(scope: str) -> str:
    """Format the human-readable location of a watch candidate.

    Args:
        scope: The candidate's watch scope (``home`` or the home-relative path
            of a curated directory).

    Returns:
        ``$HOME`` for top-level candidates, else the directory path with a
        trailing slash.
    """
    return "$HOME" if scope == "home" else f"{scope}/"


class GitReporter:
    """Present a git status-style summary of the repository's dotfiles."""

    def __init__(self, repo_dir: Path):
        """Initialize ``GitReporter``.

        Args:
            repo_dir: The git repository root containing ``dotfiles/``.
        """
        self._repo_dir = repo_dir

    def status_lines(self) -> list[str] | None:
        """Return porcelain status lines for ``dotfiles/``.

        Returns:
            The non-empty porcelain lines, or None when the directory is not a
                git work tree or git is unavailable.
        """
        if not (self._repo_dir / ".git").exists():
            logger.debug("Not a git repository; skipping git status report")
            return None
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", "--", "dotfiles"],
                cwd=self._repo_dir,
                capture_output=True,
                encoding="utf-8",
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            logger.warning(f"Could not read git status: {error}")
            return None
        return [line for line in result.stdout.splitlines() if line.strip()]

    def stage(self) -> bool:
        """Stage ``dotfiles/`` changes with ``git add``.

        Returns:
            True when staging succeeded.
        """
        try:
            subprocess.run(
                ["git", "add", "dotfiles"],
                cwd=self._repo_dir,
                capture_output=True,
                encoding="utf-8",
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            stderr = getattr(error, "stderr", None)
            logger.error(f"git add failed: {stderr or error}")
            return False
        logger.info("Staged dotfiles/ changes with git add")
        return True


class DotfilesSyncer:
    """Resolve the manifest against ``$HOME`` and sync it into the repository."""

    def __init__(
        self,
        manifest: Manifest,
        *,
        home_dir: Path,
        dotfiles_dir: Path,
        dry_run: bool = False,
        follow_symlinks: bool = False,
        prune: bool = False,
        strict_secrets: bool = False,
        stage: bool = False,
    ):
        """Initialize ``DotfilesSyncer``.

        Args:
            manifest: The parsed manifest driving the sync.
            home_dir: The source directory (normally ``$HOME``).
            dotfiles_dir: The repository directory to sync into.
            dry_run: Plan and report without mutating anything.
            follow_symlinks: Dereference symlinks into real file copies.
            prune: Delete orphaned and missing-path repository copies.
            strict_secrets: Abort the run instead of skipping files the secret
                guard flags.
            stage: Stage repository changes with ``git add`` after a real sync.
        """
        self._manifest = manifest
        self._home_dir = home_dir
        self._dotfiles_dir = dotfiles_dir
        self._dry_run = dry_run
        self._follow_symlinks = follow_symlinks
        self._prune = prune
        self._strict_secrets = strict_secrets
        self._stage = stage
        self._git = GitReporter(dotfiles_dir.parent)
        self._managed: dict[str, ManagedFile] = {}
        self._entries: list[EntryRecord] = []
        self._missing_entries: list[MissingEntry] = []
        self._watch: list[WatchCandidate] = []
        self._symlink_skips: list[PurePosixPath] = []
        self._errors: list[str] = []
        self._pattern_uses: dict[Exclude, int] = {}
        self._active_symlink_chain: set[str] = set()
        self._loop_skipped: set[PathParts] = set()

    def assessment(self) -> Assessment:
        """Resolve the manifest against ``$HOME`` and classify repository files.

        Returns:
            The full resolution outcome.
        """
        # reset accumulators so repeated calls on one instance stay independent
        self._managed = {}
        self._entries = []
        self._missing_entries = []
        self._watch = []
        self._symlink_skips = []
        self._errors = []
        self._pattern_uses = {}
        self._active_symlink_chain = set()
        self._loop_skipped = set()
        self._expand_scope(
            self._manifest.root,
            scope_base=(),
            scope_abs=self._home_dir,
            chain=(),
            optional=False,
        )
        watch = self._watch_candidates()
        orphans, stale, missing_copies, skipped_copies, allowed_orphans = (
            self._classify_repo()
        )
        return Assessment(
            managed=dict(self._managed),
            missing_entries=tuple(
                sorted(self._missing_entries, key=lambda entry: entry.rel.as_posix())
            ),
            stale=tuple(sorted(stale, key=lambda rel: rel.as_posix())),
            missing_copies=tuple(
                sorted(missing_copies, key=lambda copy: copy.rel.as_posix())
            ),
            skipped_copies=tuple(
                sorted(skipped_copies, key=lambda rel: rel.as_posix())
            ),
            orphans=tuple(sorted(orphans, key=lambda rel: rel.as_posix())),
            allowed_orphans=tuple(
                sorted(allowed_orphans, key=lambda rel: rel.as_posix())
            ),
            watch=tuple(sorted(watch, key=lambda candidate: candidate.rel.as_posix())),
            symlink_skips=tuple(
                sorted(self._symlink_skips, key=lambda rel: rel.as_posix())
            ),
            errors=tuple(self._errors),
            pattern_uses=dict(self._pattern_uses),
        )

    def build_plan(self, assessment: Assessment) -> SyncPlan:
        """Turn an assessment into the concrete set of changes to apply.

        Args:
            assessment: The resolution outcome to plan from.

        Returns:
            The planned copies and deletions.
        """
        copies = []
        skipped_secrets = []
        errors: list[str] = []
        aborted = False
        guard = SecretGuard(self._manifest.secret_patterns)
        for rel_str in sorted(assessment.managed):
            info = assessment.managed[rel_str]
            repo_path = self._dotfiles_dir / info.rel
            if repo_path.is_symlink():
                errors.append(f"{info.rel}: repository path is a symlink")
                continue
            if not repo_path.exists() or repo_path.is_dir():
                # a repo directory holding this path is stale; execute deletes
                # before copies, and fails loudly if orphan leftovers keep the
                # directory alive
                action = FileAction(rel=info.rel, source=info.source, action="add")
            else:
                try:
                    needs_copy = self._needs_copy(info.source, repo_path)
                except OSError as error:
                    errors.append(
                        f"{info.rel}: cannot compare with repo copy: {error}"
                    )
                    continue
                if not needs_copy:
                    continue
                action = FileAction(rel=info.rel, source=info.source, action="modify")

            findings = guard.scan(info.source)
            if "unreadable" in findings:
                # an unscannable file must never be synced silently
                errors.append(f"{info.rel}: cannot read file for secret scan")
                continue
            if findings:
                message = (
                    f"{info.rel}: possible secret ({', '.join(findings)}); "
                    "file will not be synced"
                )
                if self._strict_secrets:
                    errors.append(message)
                    aborted = True
                    continue
                logger.warning(f"Skipping file: {message}")
                skipped_secrets.append(info.rel)
                continue
            copies.append(action)

        prune_deletes: list[DeleteAction] = []
        if self._prune:
            prune_deletes.extend(
                DeleteAction(rel=rel, reason="prune-orphan")
                for rel in assessment.orphans
            )
            prune_deletes.extend(
                DeleteAction(rel=copy.rel, reason="prune-missing")
                for copy in assessment.missing_copies
                if not copy.optional
            )
            prune_deletes.sort(key=lambda action: action.rel.as_posix())

        return SyncPlan(
            copies=tuple(copies),
            mirror_deletes=tuple(
                DeleteAction(rel=rel, reason="delete") for rel in assessment.stale
            ),
            prune_deletes=tuple(prune_deletes),
            skipped_secrets=tuple(sorted(skipped_secrets)),
            aborted=aborted,
            errors=tuple(errors),
        )

    def execute(self, plan: SyncPlan) -> None:
        """Apply a plan, unless this is a dry run.

        Args:
            plan: The plan to apply.
        """
        if self._dry_run:
            logger.info("Dry run: no changes were made")
            return

        # deletes run before copies so that file<->directory transitions in
        # $HOME are reconciled within a single run
        for delete in (*plan.mirror_deletes, *plan.prune_deletes):
            repo_path = self._dotfiles_dir / delete.rel
            try:
                if repo_path.is_dir() and not repo_path.is_symlink():
                    raise IsADirectoryError("repository path is a directory")
                repo_path.unlink()
                self._remove_empty_parents(repo_path.parent)
            except OSError as error:
                self._errors.append(f"delete {delete.rel}: {error}")
                logger.error(f"Failed to delete {delete.rel}: {error}")

        for action in plan.copies:
            repo_path = self._dotfiles_dir / action.rel
            if not self._repo_ancestors_are_real(repo_path, action.rel):
                continue
            try:
                if repo_path.is_dir() and not repo_path.is_symlink():
                    # leftover from a replaced directory; rmdir fails loudly
                    # when orphaned files keep it alive
                    repo_path.rmdir()
                repo_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(action.source, repo_path)
            except OSError as error:
                self._errors.append(f"copy {action.rel}: {error}")
                logger.error(f"Failed to copy {action.rel}: {error}")

    def run(self) -> int:
        """Run a full sync: resolve, plan, report, and execute.

        Returns:
            Process exit code: 1 on errors, 2 when a dry run found pending
                changes, 0 otherwise (a successful sync exits 0 whether or not
                changes were applied).
        """
        assessment = self.assessment()
        plan = self.build_plan(assessment)
        self._report(assessment, plan)
        if not plan.aborted:
            self.execute(plan)
        if not self._dry_run and not plan.aborted:
            self._git_summary()
            if self._stage:
                self._git_stage()
        return self._exit_code(plan, executed=not self._dry_run)

    def status(self) -> int:
        """Report pending changes, missing entries, and orphans without syncing.

        Returns:
            Process exit code: 1 on errors, 0 otherwise.
        """
        assessment = self.assessment()
        plan = self.build_plan(assessment)
        self._report(assessment, plan)
        return 1 if assessment.errors else 0

    def check(self) -> int:
        """Terse, exit-code-driven pending-change check for cron and CI.

        Returns:
            Process exit code: 1 on errors, 2 when changes are pending,
            0 when everything is in sync.
        """
        assessment = self.assessment()
        plan = self.build_plan(assessment)
        self._report(assessment, plan, terse=True)
        return self._exit_code(plan, executed=False)

    def discover(self) -> int:
        """Audit untracked candidates from both watch scopes without syncing.

        Returns:
            Process exit code: 1 on errors, 0 otherwise.
        """
        assessment = self.assessment()
        logger.info(f"Untracked candidates: {len(assessment.watch)}")
        for candidate in assessment.watch:
            logger.info(
                f"  {candidate.rel} (in {_watch_scope_label(candidate.scope)})"
            )
        for message in assessment.errors:
            logger.error(message)
        self._warn_unused_patterns(assessment)
        return 1 if assessment.errors else 0

    def _expand_scope(
        self,
        scope: Scope,
        scope_base: PathParts,
        scope_abs: Path,
        chain: ExcludeChain,
        optional: bool,
    ) -> None:
        """Expand a scope's include items against a directory.

        Args:
            scope: The scope to expand.
            scope_base: Home-relative components of the scope's directory.
            scope_abs: Absolute path of the scope's directory.
            chain: Exclude scopes enclosing this one, root first.
            optional: Whether an enclosing entry was marked ``optional``.
        """
        item_chain = (*chain, (scope_base, scope.exclude))
        for item in scope.include:
            self._expand_item(
            item=item,
            scope_base=scope_base,
            scope_abs=scope_abs,
            chain=item_chain,
            optional=optional,
        )

    def _expand_item(
        self,
        item: Include,
        scope_base: PathParts,
        scope_abs: Path,
        chain: ExcludeChain,
        optional: bool,
    ) -> None:
        """Expand a single include item against its parent directory.

        Args:
            item: The item to expand.
            scope_base: Home-relative components of the item's scope directory.
            scope_abs: Absolute path of the item's scope directory.
            chain: Exclude scopes enclosing the item, including its own scope.
            optional: Whether an enclosing entry was marked ``optional``.
        """
        if item.glob:
            self._glob_step(
            item=item,
            index=0,
            cur_abs=scope_abs,
            cur_parts=scope_base,
            chain=chain,
            optional=optional,
        )
            return

        target_parts = scope_base + item.parts
        target_abs = scope_abs.joinpath(*item.parts)
        entry_optional = optional or item.optional

        if target_abs.is_symlink():
            self._handle_symlink(
                link_abs=target_abs,
                link_parts=target_parts,
                chain=chain,
                scope=item.scope,
                optional=entry_optional,
            )
            return
        if target_abs.is_dir():
            self._register_entry(
                item,
                parts=target_parts,
                abs_path=target_abs,
                kind="dir",
                chain=chain,
            )
            self._walk_dir(
                dir_abs=target_abs,
                dir_parts=target_parts,
                chain=chain,
                scope=item.scope,
                optional=entry_optional,
            )
            return
        if target_abs.is_file():
            self._register_entry(
                item,
                parts=target_parts,
                abs_path=target_abs,
                kind="file",
                chain=chain,
            )
            self._record_file(target_abs, target_parts)
            return
        if not target_abs.exists():
            self._register_entry(
                item,
                parts=target_parts,
                abs_path=target_abs,
                kind="missing",
                chain=chain,
            )
            self._missing_entries.append(
                MissingEntry(rel=PurePosixPath(*target_parts), optional=entry_optional)
            )
            return
        self._errors.append(f"{'/'.join(target_parts)}: not a regular file")

    def _walk_dir(
        self,
        dir_abs: Path,
        dir_parts: PathParts,
        chain: ExcludeChain,
        scope: Scope | None,
        optional: bool,
    ) -> None:
        """Walk a directory entry, either wholly or through a nested scope.

        Args:
            dir_abs: Absolute path of the directory.
            dir_parts: Home-relative components of the directory.
            chain: Exclude scopes enclosing the directory.
            scope: The entry's nested scope, if any.
            optional: Whether the entry was marked ``optional``.
        """
        if scope is not None and scope.include:
            self._expand_scope(
                scope=scope,
                scope_base=dir_parts,
                scope_abs=dir_abs,
                chain=chain,
                optional=optional,
            )
            return
        if scope is not None:
            # exclude-only nested scope: walk the whole directory, prunes apply
            chain = (*chain, (dir_parts, scope.exclude))

        for child in self._sorted_children(dir_abs):
            child_parts = dir_parts + (child.name,)
            if self._match_exclude(parts=child_parts, chain=chain) is not None:
                continue
            if child.is_symlink():
                self._handle_symlink(
                    link_abs=child,
                    link_parts=child_parts,
                    chain=chain,
                    scope=None,
                    optional=optional,
                )
            elif child.is_dir():
                self._walk_dir(
                    dir_abs=child,
                    dir_parts=child_parts,
                    chain=chain,
                    scope=None,
                    optional=optional,
                )
            elif child.is_file():
                self._record_file(child, child_parts)
            else:
                self._errors.append(f"{'/'.join(child_parts)}: not a regular file")

    def _glob_step(
        self,
        item: Include,
        index: int,
        cur_abs: Path,
        cur_parts: PathParts,
        chain: ExcludeChain,
        optional: bool,
    ) -> None:
        """Expand a glob item component by component.

        Args:
            item: The glob item being expanded.
            index: Index of the component to match against ``cur_abs``.
            cur_abs: Absolute path matched so far.
            cur_parts: Home-relative components matched so far.
            chain: Exclude scopes enclosing the item.
            optional: Whether an enclosing entry was marked ``optional``.
        """
        parts = item.parts
        if index == len(parts):
            self._include_glob_match(
            item=item,
            target_abs=cur_abs,
            target_parts=cur_parts,
            chain=chain,
            optional=optional,
        )
            return

        component = parts[index]
        if component == "**":
            # zero segments, then descend into each unpruned subdirectory
            self._glob_step(
                item=item,
                index=index + 1,
                cur_abs=cur_abs,
                cur_parts=cur_parts,
                chain=chain,
                optional=optional,
            )
            if cur_abs.is_dir() and not cur_abs.is_symlink():
                for child in self._sorted_children(cur_abs):
                    child_parts = cur_parts + (child.name,)
                    if self._match_exclude(parts=child_parts, chain=chain) is not None:
                        continue
                    if child.is_symlink() and index + 1 < len(parts):
                        self._glob_symlink_step(
                            item=item,
                            next_index=index,
                            link_abs=child,
                            link_parts=child_parts,
                            chain=chain,
                            optional=optional,
                        )
                        continue
                    self._glob_step(
                        item=item,
                        index=index,
                        cur_abs=child,
                        cur_parts=child_parts,
                        chain=chain,
                        optional=optional,
                    )
        elif _GLOB_CHARS.search(component):
            for child in self._sorted_children(cur_abs):
                if not fnmatch.fnmatch(child.name, component):
                    continue
                child_parts = cur_parts + (child.name,)
                if self._match_exclude(parts=child_parts, chain=chain) is not None:
                    continue
                if child.is_symlink() and index + 1 < len(parts):
                    self._glob_symlink_step(
                        item=item,
                        next_index=index + 1,
                        link_abs=child,
                        link_parts=child_parts,
                        chain=chain,
                        optional=optional,
                    )
                    continue
                self._glob_step(
                    item=item,
                    index=index + 1,
                    cur_abs=child,
                    cur_parts=child_parts,
                    chain=chain,
                    optional=optional,
                )
        else:
            child = cur_abs / component
            if not child.exists() and not child.is_symlink():
                return
            if self._match_exclude(parts=cur_parts + (component,), chain=chain) is not None:
                return
            if child.is_symlink() and index + 1 < len(parts):
                self._glob_symlink_step(
                    item=item,
                    next_index=index + 1,
                    link_abs=child,
                    link_parts=cur_parts + (component,),
                    chain=chain,
                    optional=optional,
                )
                return
            self._glob_step(
                item=item,
                index=index + 1,
                cur_abs=child,
                cur_parts=cur_parts + (component,),
                chain=chain,
                optional=optional,
            )

    def _glob_symlink_step(
        self,
        item: Include,
        next_index: int,
        link_abs: Path,
        link_parts: PathParts,
        chain: ExcludeChain,
        optional: bool,
    ) -> None:
        """Continue a glob expansion across a mid-path symlink component.

        Applies the same semantics as ``_handle_symlink``: broken links are
        errors, unfollowed links are skipped with a note, and followed
        directory targets continue the component match from the resolved path
        under loop protection.

        Args:
            item: The glob item being expanded.
            next_index: Index of the component to match from the link target.
            link_abs: Absolute path of the mid-path symlink.
            link_parts: Home-relative components of the symlink.
            chain: Exclude scopes enclosing the item.
            optional: Whether an enclosing entry was marked ``optional``.
        """
        rel_str = "/".join(link_parts)
        if not link_abs.exists():
            self._errors.append(f"{rel_str}: broken symlink")
            return
        if not self._follow_symlinks:
            self._symlink_skips.append(PurePosixPath(*link_parts))
            return
        resolved = link_abs.resolve()
        if not resolved.is_dir():
            self._glob_step(
                item=item,
                index=next_index,
                cur_abs=resolved,
                cur_parts=link_parts,
                chain=chain,
                optional=optional,
            )
            return
        key = str(resolved)
        if key in self._active_symlink_chain:
            logger.warning(f"Symlink loop skipped: {rel_str}")
            self._loop_skipped.add(link_parts)
            return
        self._active_symlink_chain.add(key)
        try:
            self._glob_step(
                item=item,
                index=next_index,
                cur_abs=resolved,
                cur_parts=link_parts,
                chain=chain,
                optional=optional,
            )
        finally:
            self._active_symlink_chain.discard(key)

    def _include_glob_match(
        self,
        item: Include,
        target_abs: Path,
        target_parts: PathParts,
        chain: ExcludeChain,
        optional: bool,
    ) -> None:
        """Handle a path fully matched by a glob item.

        Args:
            item: The glob item that matched.
            target_abs: Absolute path of the matched path.
            target_parts: Home-relative components of the matched path.
            chain: Exclude scopes enclosing the item.
            optional: Whether an enclosing entry was marked ``optional``.
        """
        entry_optional = optional or item.optional
        if target_abs.is_symlink():
            self._handle_symlink(
                link_abs=target_abs,
                link_parts=target_parts,
                chain=chain,
                scope=None,
                optional=entry_optional,
            )
            return
        if target_abs.is_dir():
            # glob items cannot carry a nested scope (parse-time rejection)
            self._walk_dir(
                dir_abs=target_abs,
                dir_parts=target_parts,
                chain=chain,
                scope=None,
                optional=entry_optional,
            )
            return
        if target_abs.is_file():
            self._record_file(target_abs, target_parts)
        elif not target_abs.exists():
            logger.debug(f"Glob match vanished during walk: {'/'.join(target_parts)}")
        else:
            self._errors.append(f"{'/'.join(target_parts)}: not a regular file")

    def _handle_symlink(
        self,
        link_abs: Path,
        link_parts: PathParts,
        chain: ExcludeChain,
        scope: Scope | None,
        optional: bool,
    ) -> None:
        """Handle a symlink encountered during expansion.

        Broken symlinks are recorded as errors. Otherwise the link is skipped
        with a note, unless ``--follow-symlinks`` dereferences it.

        Args:
            link_abs: Absolute path of the symlink.
            link_parts: Home-relative components of the symlink.
            chain: Exclude scopes enclosing the link.
            scope: Nested scope to apply if the target is a directory.
            optional: Whether the entry was marked ``optional``.
        """
        rel_str = "/".join(link_parts)
        if not link_abs.exists():
            self._errors.append(f"{rel_str}: broken symlink")
            return
        if not self._follow_symlinks:
            self._symlink_skips.append(PurePosixPath(*link_parts))
            return

        resolved = link_abs.resolve()
        if resolved.is_dir():
            key = str(resolved)
            if key in self._active_symlink_chain:
                # the target is an ancestor of the current walk: a genuine loop
                logger.warning(f"Symlink loop skipped: {rel_str}")
                self._loop_skipped.add(link_parts)
                return
            self._active_symlink_chain.add(key)
            try:
                self._walk_dir(
                    dir_abs=resolved,
                    dir_parts=link_parts,
                    chain=chain,
                    scope=scope,
                    optional=optional,
                )
            finally:
                self._active_symlink_chain.discard(key)
        elif resolved.is_file():
            self._record_file(resolved, link_parts)
        else:
            self._errors.append(f"{rel_str}: symlink target is not a regular file")

    def _register_entry(
        self,
        item: Include,
        *,
        parts: PathParts,
        abs_path: Path,
        kind: Literal["dir", "file", "missing"],
        chain: ExcludeChain,
    ) -> None:
        """Record a literal entry for repository-side classification.

        Args:
            item: The include item being expanded.
            parts: Home-relative components of the entry.
            abs_path: Absolute path of the entry in ``$HOME``.
            kind: ``dir``, ``file``, or ``missing``.
            chain: Exclude scopes enclosing the entry.
        """
        self._entries.append(
            EntryRecord(
                parts=parts,
                abs=abs_path,
                kind=kind,
                scope=item.scope,
                chain=chain,
            )
        )

    def _record_file(self, source: Path, parts: PathParts) -> None:
        """Record a managed file, keeping the first covering entry on overlap.

        Args:
            source: Absolute path to read the file's content from.
            parts: Home-relative components of the file.
        """
        key = "/".join(parts)
        if key in self._managed:
            logger.debug(f"Duplicate include for {key}; keeping the first entry")
            return
        self._managed[key] = ManagedFile(rel=PurePosixPath(*parts), source=source)

    def _match_exclude(
        self,
        parts: PathParts,
        chain: ExcludeChain,
    ) -> Exclude | None:
        """Find the first exclude matching a path or one of its ancestors.

        Matching uses search semantics against paths relative to each scope's
        base, and records the pattern as used.

        Args:
            parts: Home-relative components of the candidate path.
            chain: Exclude scopes ``(base, excludes)`` to test against.

        Returns:
            The matching exclude, or None when nothing matches.
        """
        for scope_base, excludes in chain:
            relative = parts[len(scope_base) :]
            for depth in range(1, len(relative) + 1):
                candidate = "/".join(relative[:depth])
                for exclude in excludes:
                    if exclude.pattern.search(candidate):
                        self._pattern_uses[exclude] = (
                            self._pattern_uses.get(exclude, 0) + 1
                        )
                        return exclude
        return None

    def _watch_candidates(self) -> list[WatchCandidate]:
        """Collect untracked candidates from both watch scopes.

        Scans top-level ``$HOME`` dot-entries and the contents of curated
        directory includes (those declaring a nested ``include:`` scope),
        silencing candidates covered by the manifest or matched by an exclude
        of their scope or any enclosing scope.

        Returns:
            The remaining untracked candidates.
        """
        candidates = []
        root_excludes = (((), self._manifest.root.exclude),)

        for child in self._sorted_children(self._home_dir):
            if not child.name.startswith("."):
                continue
            if self._name_is_covered(child.name, self._manifest.root):
                continue
            if self._match_exclude(parts=(child.name,), chain=root_excludes) is not None:
                continue
            candidates.append(
                WatchCandidate(rel=PurePosixPath(child.name), scope="home")
            )

        for record in self._entries:
            if record.kind != "dir" or record.scope is None or not record.scope.include:
                continue
            # the record's chain holds every enclosing scope's excludes (root
            # first); the entry's own nested scope completes the set
            child_chain = (*record.chain, (record.parts, record.scope.exclude))
            for child in self._sorted_children(record.abs):
                if self._name_is_covered(child.name, record.scope):
                    continue
                child_parts = record.parts + (child.name,)
                if self._match_exclude(parts=child_parts, chain=child_chain) is not None:
                    continue
                candidates.append(
                    WatchCandidate(
                        rel=PurePosixPath(*child_parts),
                        scope="/".join(record.parts),
                    )
                )
        return candidates

    def _name_is_covered(self, name: str, scope: Scope) -> bool:
        """Return whether a name is covered by any include item of a scope.

        Args:
            name: The entry's name within the scope's directory.
            scope: The scope whose include items to test.

        Returns:
            True when any item's first component covers the name.
        """
        for item in scope.include:
            if not item.parts:
                return True
            first = item.parts[0]
            if _GLOB_CHARS.search(first):
                if fnmatch.fnmatch(name, first):
                    return True
            elif name == first:
                return True
        return False

    def _classify_repo(
        self,
    ) -> tuple[
        list[PurePosixPath],
        list[PurePosixPath],
        list[MissingCopy],
        list[PurePosixPath],
    ]:
        """Classify every repository file against the resolved manifest set.

        Returns:
            Orphaned files, stale files within live directory entries,
            repository copies of entries missing in ``$HOME``, repository
            files whose ``$HOME`` counterpart is an unfollowed symlink, and
            allowed orphans beneath ``allow_orphan`` excludes.
        """
        orphans, stale, missing_copies, skipped_copies, allowed = [], [], [], [], []
        for rel_str, _ in sorted(self._scan_repo().items()):
            if rel_str in self._managed:
                continue
            parts = tuple(rel_str.split("/"))
            kind, optional = self._classify_repo_path(parts)
            if kind == "stale":
                stale.append(PurePosixPath(*parts))
            elif kind == "missing":
                missing_copies.append(
                    MissingCopy(rel=PurePosixPath(*parts), optional=optional)
                )
            elif kind == "skipped":
                skipped_copies.append(PurePosixPath(*parts))
            elif kind == "allowed_orphan":
                allowed.append(PurePosixPath(*parts))
            else:
                orphans.append(PurePosixPath(*parts))
        return orphans, stale, missing_copies, skipped_copies, allowed

    def _classify_repo_path(self, parts: PathParts) -> tuple[str, bool]:
        """Classify one repository file by walking the manifest recursively.

        Mirrors the home-side expansion: literal items cover their path and
        everything beneath it, curated scopes cover only their nested items,
        and excludes prune at the scope where they are declared.

        Args:
            parts: Repository-relative components of the file (mirroring the
                home-relative structure).

        Returns:
            A ``(kind, optional)`` pair where kind is ``stale``, ``missing``,
            ``skipped``, ``allowed_orphan``, or ``orphan``.
        """
        result = self._classify_scope(
            self._manifest.root,
            scope_base=(),
            parts=parts,
            optional=False,
            chain=(),
        )
        return result if result is not None else ("orphan", False)

    def _classify_scope(
        self,
        scope: Scope,
        scope_base: PathParts,
        parts: PathParts,
        optional: bool,
        chain: ExcludeChain,
    ) -> tuple[str, bool] | None:
        """Classify a repository path against one scope's include items.

        Args:
            scope: The scope whose items to test.
            scope_base: Home-relative components of the scope's directory.
            parts: Home-relative components of the repository file.
            optional: Whether an enclosing entry was marked ``optional``.
            chain: Exclude scopes enclosing this one, root first.

        Returns:
            A ``(kind, optional)`` pair when an item covers the path, else
            None when the path is unmanaged by this scope.
        """
        item_chain = (*chain, (scope_base, scope.exclude))
        matched = self._match_exclude(parts=parts, chain=item_chain)
        if matched is not None:
            if matched.allow_orphan:
                return ("allowed_orphan", optional)
            return None
        rel = parts[len(scope_base) :]
        for item in scope.include:
            item_optional = optional or item.optional
            if item.glob:
                # glob selection is filesystem-derived: a repository file the
                # home side does not select is simply unmanaged
                continue
            if rel[: len(item.parts)] != item.parts:
                continue
            target_base = scope_base + item.parts
            target_abs = (
                self._home_dir.joinpath(*target_base) if target_base else self._home_dir
            )
            if target_abs.is_symlink() and not self._follow_symlinks:
                # the entry (or an ancestor of the repo file) is an unfollowed
                # symlink: its repo copies are kept untouched
                return ("skipped", item_optional)
            if len(rel) == len(item.parts):
                # the repository path is the item path itself: either the entry
                # is missing in $HOME, or the repo file clashes with a home dir
                if target_abs.exists():
                    return ("stale", item_optional)
                return ("missing", item_optional)
            if item.scope is not None and item.scope.include:
                nested = self._classify_scope(
                    item.scope,
                    scope_base=target_base,
                    parts=parts,
                    optional=item_optional,
                    chain=item_chain,
                )
                if nested is not None:
                    return nested
                continue
            chain_for_domain = item_chain
            if item.scope is not None:
                # exclude-only nested scope: its prunes apply to this domain
                chain_for_domain = (*item_chain, (target_base, item.scope.exclude))
                matched = self._match_exclude(parts=parts, chain=chain_for_domain)
                if matched is not None:
                    if matched.allow_orphan:
                        return ("allowed_orphan", item_optional)
                    return None
            # whole-directory domain: missing dir means the whole entry is gone
            if not target_abs.exists() and not target_abs.is_symlink():
                return ("missing", item_optional)
            file_abs = self._home_dir.joinpath(*parts)
            if file_abs.is_symlink() and not self._follow_symlinks:
                return ("skipped", item_optional)
            if self._under_loop_skipped_link(parts):
                # the home-side walk was cut short by a symlink loop; keep the
                # repo copies rather than deleting what was never examined
                return ("skipped", item_optional)
            return ("stale", item_optional)
        return None

    def _under_loop_skipped_link(self, parts: PathParts) -> bool:
        """Return whether an ancestor of the path was skipped as a symlink loop.

        Args:
            parts: Home-relative components of the repository file.

        Returns:
            True when any proper ancestor is a loop-skipped symlink.
        """
        return any(
            parts[:depth] in self._loop_skipped for depth in range(1, len(parts))
        )

    def _scan_repo(self) -> dict[str, Path]:
        """List every repository file (and symlink) by relative POSIX path.

        Returns:
            A mapping from relative POSIX path to absolute path.
        """
        if not self._dotfiles_dir.is_dir():
            self._errors.append(
                f"{self._dotfiles_dir}: repository directory is missing"
            )
            return {}
        files = {}
        for path in sorted(self._dotfiles_dir.rglob("*")):
            if path.is_dir() and not path.is_symlink():
                continue
            files[path.relative_to(self._dotfiles_dir).as_posix()] = path
        return files

    def _sorted_children(self, dir_abs: Path) -> list[Path]:
        """List a directory's children, sorted by name.

        Args:
            dir_abs: Absolute path of the directory.

        Returns:
            The children, or an empty list if the directory is unreadable.
        """
        try:
            return sorted(dir_abs.iterdir(), key=lambda child: child.name)
        except OSError as error:
            self._errors.append(f"{dir_abs}: cannot list directory: {error}")
            return []

    def _needs_copy(self, home_path: Path, repo_path: Path) -> bool:
        """Compare a home file against its repository copy.

        Uses content plus mode plus mtime, so files already in sync are never
        re-copied (avoiding gratuitous mtime churn).

        Args:
            home_path: Absolute path of the source file.
            repo_path: Absolute path of the repository copy.

        Returns:
            True when the repository copy is missing or differs.
        """
        home_stat = home_path.stat()
        repo_stat = repo_path.stat()
        if home_stat.st_mode & 0o7777 != repo_stat.st_mode & 0o7777:
            return True
        if home_stat.st_mtime_ns != repo_stat.st_mtime_ns:
            return True
        if home_stat.st_size != repo_stat.st_size:
            return True
        return not filecmp.cmp(home_path, repo_path, shallow=False)

    def _repo_ancestors_are_real(self, repo_path: Path, rel: PurePosixPath) -> bool:
        """Return whether no ancestor of the path inside dotfiles/ is a symlink.

        Guards copies from being redirected outside the repository through a
        planted or mistaken symlinked directory.

        Args:
            repo_path: Absolute repository path about to be written.
            rel: Home-relative path of the managed file, for messages.

        Returns:
            True when every existing ancestor within dotfiles/ is a real
                directory.
        """
        probe = self._dotfiles_dir
        for part in repo_path.relative_to(self._dotfiles_dir).parts[:-1]:
            probe = probe / part
            if probe.is_symlink():
                self._errors.append(
                    f"{rel}: repository ancestor {probe.relative_to(self._dotfiles_dir)} "
                    "is a symlink; refusing to write through it"
                )
                logger.error(
                    f"Refusing to copy {rel}: repository ancestor "
                    f"{probe.relative_to(self._dotfiles_dir)} is a symlink"
                )
                return False
        return True

    def _remove_empty_parents(self, start: Path) -> None:
        """Remove now-empty directories between a deleted file and the repo root.

        Args:
            start: The parent directory of the deleted file.
        """
        parent = start
        while (
            parent != self._dotfiles_dir
            and parent.is_dir()
            and not any(parent.iterdir())
        ):
            parent.rmdir()
            parent = parent.parent

    def _report(
        self, assessment: Assessment, plan: SyncPlan, terse: bool = False
    ) -> None:
        """Log the full resolution and plan outcome.

        Args:
            assessment: The resolution outcome.
            plan: The planned changes.
            terse: Skip per-file action lines (for ``--check``).
        """
        logger.info(
            f"Sync plan: {len(plan.copies)} to copy, "
            f"{len(plan.mirror_deletes)} to delete, "
            f"{len(plan.prune_deletes)} to prune"
        )
        if not terse:
            for action in plan.copies:
                logger.info(f"{action.action}: {action.rel}")
            for delete in (*plan.mirror_deletes, *plan.prune_deletes):
                logger.info(f"{delete.reason}: {delete.rel}")

        for entry in assessment.missing_entries:
            if not entry.optional:
                logger.warning(f"Missing in $HOME: {entry.rel}")
        for rel in assessment.orphans:
            logger.warning(f"Orphaned repo file: {rel}")
        for rel in assessment.allowed_orphans:
            logger.debug(f"Allowed orphan repo file: {rel}")
        for candidate in assessment.watch:
            logger.warning(
                f"Untracked dotfile candidate: {candidate.rel} "
                f"(in {_watch_scope_label(candidate.scope)})"
            )
        for rel in assessment.symlink_skips:
            logger.warning(f"Symlink skipped (use --follow-symlinks to sync): {rel}")
        for rel in assessment.skipped_copies:
            logger.warning(
                f"Repo copy kept (its $HOME counterpart is an unfollowed symlink "
                f"or symlink loop): {rel}"
            )
        for message in (*assessment.errors, *plan.errors):
            logger.error(message)

        self._warn_unused_patterns(assessment)

    def _warn_unused_patterns(self, assessment: Assessment) -> None:
        """Warn about exclude patterns that matched nothing during the run.

        Args:
            assessment: The resolution outcome holding the usage counts.
        """
        unused = self._unused_patterns(assessment)
        if unused:
            joined = ", ".join(repr(pattern) for pattern in unused)
            logger.warning(
                f"Unused exclude pattern(s): {joined} "
                "(mark optional to allow matching nothing)"
            )

    def _unused_patterns(self, assessment: Assessment) -> list[str]:
        """Collect exclude patterns that matched nothing during the run.

        Args:
            assessment: The resolution outcome holding the usage counts.

        Returns:
            The raw pattern texts of unused, non-optional excludes.
        """
        unused = []
        for exclude in self._iter_excludes(self._manifest.root):
            if assessment.pattern_uses.get(exclude, 0) == 0 and not exclude.optional:
                unused.append(exclude.source)
        return unused

    def _iter_excludes(self, scope: Scope) -> Iterator[Exclude]:
        """Yield every exclude in a scope and its nested scopes.

        Args:
            scope: The scope to walk.

        Yields:
            Each exclude rule found.
        """
        yield from scope.exclude
        for item in scope.include:
            if item.scope is not None:
                yield from self._iter_excludes(item.scope)

    def _exit_code(self, plan: SyncPlan, *, executed: bool) -> int:
        """Compute the process exit code for a plan.

        Args:
            plan: The plan that was (or would have been) executed.
            executed: Whether the plan was actually applied; an unapplied plan
                with changes reports them as pending.

        Returns:
            1 on errors, 2 when changes are pending, else 0.
        """
        if self._errors or plan.errors:
            return 1
        if not executed and (plan.copies or plan.mirror_deletes or plan.prune_deletes):
            return 2
        return 0

    def _git_summary(self) -> None:
        """Log a git status-style summary of the repository's dotfiles."""
        lines = self._git.status_lines()
        if lines is None:
            return
        logger.info("Git status of dotfiles/:")
        for line in lines:
            logger.info(line)

    def _git_stage(self) -> None:
        """Stage repository changes with ``git add`` after a real sync."""
        if not self._git.stage():
            self._errors.append("git add failed")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list; defaults to ``sys.argv[1:]``.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Sync dotfiles from $HOME into the repository's dotfiles/ directory.",
    )
    parser.add_argument(
        "--config",
        action="store",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        metavar="<PATH>",
        help=f"Path to the YAML manifest (default: {DEFAULT_CONFIG_PATH.name}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan and print every copy/delete without mutating anything.",
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--status",
        action="store_true",
        help="Report modified/unmanaged/missing/orphaned files without syncing.",
    )
    modes.add_argument(
        "--check",
        action="store_true",
        help="Terse dry run driven by the exit code (for cron/CI).",
    )
    modes.add_argument(
        "--discover",
        action="store_true",
        help="Audit untracked candidates in both watch scopes; report only.",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Delete orphaned repo files and repo copies of entries missing in $HOME.",
    )
    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Dereference symlinks into real file copies instead of skipping them.",
    )
    parser.add_argument(
        "--strict-secrets",
        action="store_true",
        help="Abort the run when the secret guard flags a file.",
    )
    parser.add_argument(
        "--stage",
        action="store_true",
        help="Stage repository changes with git add after a real sync.",
    )
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    verbosity.add_argument(
        "--quiet",
        action="store_true",
        help="Restrict logging to warnings and errors.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Argument list; defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code: 0 on success, 1 on error, 2 when changes are
        pending (dry runs and ``--check`` only).
    """
    args = parse_args(argv)
    _configure_logging(args.verbose, args.quiet)

    report_only = args.status or args.check or args.discover
    if args.prune and report_only:
        logger.error("--prune cannot be combined with report-only modes")
        return 1
    if args.stage and report_only:
        logger.warning("--stage has no effect with report-only modes; ignoring it")
    if args.stage and args.dry_run:
        logger.warning("--stage has no effect with --dry-run; ignoring it")

    try:
        manifest = Manifest.load(args.config)
    except ConfigError as error:
        logger.error(str(error))
        return 1

    syncer = DotfilesSyncer(
        manifest,
        home_dir=HOME_DIR,
        dotfiles_dir=DOTFILES_DIR,
        dry_run=args.dry_run,
        follow_symlinks=args.follow_symlinks,
        prune=args.prune,
        strict_secrets=args.strict_secrets,
        stage=args.stage,
    )
    if args.status:
        return syncer.status()
    if args.check:
        return syncer.check()
    if args.discover:
        return syncer.discover()
    return syncer.run()


if __name__ == "__main__":
    raise SystemExit(main())
