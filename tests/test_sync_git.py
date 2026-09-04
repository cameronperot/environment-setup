"""Tests for the git status report and --stage."""

import logging
import os
import subprocess

from conftest import build_env, make_syncer

import sync_dotfiles


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
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    subprocess.run(["git", "init", "-q"], cwd=repo_dir, check=True, env=identity)
    subprocess.run(["git", "add", "dotfiles"], cwd=repo_dir, check=True, env=identity)
    subprocess.run(
        ["git", "commit", "-q", "-m", "init"], cwd=repo_dir, check=True, env=identity
    )


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


def test_status_lines_reports_nothing_when_git_fails(tmp_path, monkeypatch, caplog):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)

    def boom(*args, **kwargs):
        raise subprocess.CalledProcessError(128, "git", stderr="fatal: broken")

    monkeypatch.setattr(sync_dotfiles.subprocess, "run", boom)

    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        lines = sync_dotfiles.GitReporter(repo).status_lines()

    assert lines is None
    assert "Could not read git status" in caplog.text


def test_status_lines_reports_nothing_when_git_is_missing(
    tmp_path, monkeypatch, caplog
):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)

    def missing(*args, **kwargs):
        raise OSError(2, "No such file or directory")

    monkeypatch.setattr(sync_dotfiles.subprocess, "run", missing)

    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        lines = sync_dotfiles.GitReporter(repo).status_lines()

    assert lines is None
    assert "Could not read git status" in caplog.text


def test_stage_failure_fails_the_run(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [f.txt]\n",
        home_files={"f.txt": "new"},
        repo_files={"f.txt": "old"},
    )
    init_git_repo(env.dotfiles.parent)
    # an existing index.lock makes git add fail for any user, root included
    (env.dotfiles.parent / ".git/index.lock").write_text("")

    with caplog.at_level(logging.ERROR, logger="sync_dotfiles"):
        exit_code = make_syncer(env, stage=True).run()

    assert exit_code == 1
    assert "git add failed" in caplog.text
