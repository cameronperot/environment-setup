"""Tests for CLI modes, the untracked watch, exit codes, and the git report."""

import logging
import os
import subprocess

import pytest
from conftest import build_env, make_syncer

from sync_dotfiles import main, parse_args


def init_git_repo(repo_dir):
    """Initialize a git repository with an identity and commit dotfiles/.

    Args:
        repo_dir: The repository root containing ``dotfiles/``.
    """
    identity = {
        **os.environ,
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    subprocess.run(["git", "init", "-q"], cwd=repo_dir, check=True, env=identity)
    subprocess.run(["git", "add", "dotfiles"], cwd=repo_dir, check=True, env=identity)
    subprocess.run(
        ["git", "commit", "-q", "-m", "init"], cwd=repo_dir, check=True, env=identity
    )


def test_check_exits_two_when_changes_are_pending_and_stays_terse(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [f.txt, live]\n",
        home_files={"f.txt": "new", "live/a.txt": "a"},
        repo_files={"f.txt": "old"},
    )

    with caplog.at_level(logging.INFO, logger="sync_dotfiles"):
        exit_code = make_syncer(env).check()

    assert exit_code == 2
    assert "Sync plan: 2 to copy" in caplog.text
    assert "add: f.txt" not in caplog.text


def test_check_exits_zero_when_everything_is_in_sync(tmp_path):
    env = build_env(
        tmp_path,
        "include: [f.txt]\n",
        home_files={"f.txt": "same"},
        repo_files={"f.txt": "same"},
    )
    os.utime(env.home / "f.txt", ns=(1000, 1000))
    os.utime(env.dotfiles / "f.txt", ns=(1000, 1000))

    assert make_syncer(env).check() == 0


def test_status_check_discover_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        parse_args(["--status", "--check"])


def test_prune_with_report_only_mode_exits_one(tmp_path):
    env = build_env(
        tmp_path,
        "include: [f.txt]\n",
        home_files={"f.txt": "f"},
        repo_files={"f.txt": "f"},
    )

    assert main(["--check", "--prune", "--config", str(env.config)]) == 1


def test_discover_reports_candidates_and_exits_zero(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [.tool]\n",
        home_files={".tool/x": "x", ".newtool/conf": "c"},
    )

    with caplog.at_level(logging.INFO, logger="sync_dotfiles"):
        exit_code = make_syncer(env).discover()

    assert exit_code == 0
    assert "Untracked candidates: 1" in caplog.text
    assert ".newtool (in $HOME)" in caplog.text


def test_run_exits_zero_after_syncing_changes(tmp_path):
    env = build_env(
        tmp_path,
        "include: [f.txt]\n",
        home_files={"f.txt": "new"},
        repo_files={"f.txt": "old"},
    )

    assert make_syncer(env).run() == 0


def test_status_exits_one_on_errors(tmp_path):
    env = build_env(
        tmp_path,
        "include: [broken]\n",
        home_files={"keep.txt": "k"},
    )
    (env.home / "broken").symlink_to(env.home / "nowhere")

    assert make_syncer(env).status() == 1


def test_discover_reports_errors_and_exits_one(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [broken]\n",
        home_files={"keep.txt": "k"},
    )
    (env.home / "broken").symlink_to(env.home / "nowhere")

    with caplog.at_level(logging.ERROR, logger="sync_dotfiles"):
        exit_code = make_syncer(env).discover()

    assert exit_code == 1
    assert "broken symlink" in caplog.text


def test_watch_reports_untracked_excluded_and_covered_entries_correctly(tmp_path):
    env = build_env(
        tmp_path,
        (
            "include:\n"
            "  - .tool\n"
            "  - path: .config\n"
            "    include: [kept]\n"
            "exclude:\n"
            "  - pattern: '^\\.ignored$'\n"
            "    optional: true\n"
        ),
        home_files={
            ".tool/x": "x",
            ".config/kept/a": "a",
            ".config/untracked/b": "b",
            ".ignored/c": "c",
            ".fresh/d": "d",
        },
    )
    assessment = make_syncer(env).assessment()

    assert [
        (candidate.rel.as_posix(), candidate.scope) for candidate in assessment.watch
    ] == [(".config/untracked", ".config"), (".fresh", "home")]


def test_watch_honors_nested_scope_excludes(tmp_path):
    env = build_env(
        tmp_path,
        (
            "include:\n"
            "  - path: .config\n"
            "    include:\n"
            "      - path: tool\n"
            "        include: [tracked]\n"
            "        exclude: ['^state$']\n"
        ),
        home_files={
            ".config/tool/tracked/a": "a",
            ".config/tool/state/db": "db",
            ".config/tool/untracked/b": "b",
        },
    )
    assessment = make_syncer(env).assessment()

    assert [(c.rel.as_posix(), c.scope) for c in assessment.watch] == [
        (".config/tool/untracked", ".config/tool")
    ]


def test_untracked_warnings_never_affect_the_exit_code(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [.tool]\n",
        home_files={".tool/x": "x", ".newtool/conf": "c"},
        repo_files={".tool/x": "x"},
    )
    os.utime(env.home / ".tool/x", ns=(1000, 1000))
    os.utime(env.dotfiles / ".tool/x", ns=(1000, 1000))

    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        exit_code = make_syncer(env).run()

    assert exit_code == 0
    assert "Untracked dotfile candidate: .newtool" in caplog.text


def test_git_report_lists_changes_after_sync(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [f.txt]\n",
        home_files={"f.txt": "new"},
        repo_files={"f.txt": "old"},
    )
    init_git_repo(env.dotfiles.parent)

    with caplog.at_level(logging.INFO, logger="sync_dotfiles"):
        assert make_syncer(env).run() == 0

    assert "Git status of dotfiles/:" in caplog.text
    assert "M dotfiles/f.txt" in caplog.text


def test_stage_stages_repository_changes(tmp_path):
    env = build_env(
        tmp_path,
        "include: [f.txt]\n",
        home_files={"f.txt": "new"},
        repo_files={"f.txt": "old"},
    )
    init_git_repo(env.dotfiles.parent)

    assert make_syncer(env, stage=True).run() == 0

    status = subprocess.run(
        ["git", "status", "--porcelain", "--", "dotfiles"],
        cwd=env.dotfiles.parent,
        capture_output=True,
        encoding="utf-8",
        check=True,
    ).stdout
    assert status.startswith("M  dotfiles/f.txt")


def test_git_report_is_skipped_outside_a_repository(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [f.txt]\n",
        home_files={"f.txt": "new"},
        repo_files={"f.txt": "old"},
    )

    with caplog.at_level(logging.INFO, logger="sync_dotfiles"):
        assert make_syncer(env).run() == 0

    assert "Git status" not in caplog.text
