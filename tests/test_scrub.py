"""Tests for the repository-side scrub rules (e.g. .gitconfig signingkey)."""

import logging

from conftest import build_env, make_syncer, snapshot


def test_sync_redacts_signingkey_in_repo_copy_but_not_home(tmp_path):
    env = build_env(
        tmp_path,
        "include: [.gitconfig]\n",
        home_files={".gitconfig": "[user]\n    signingkey = ssh-ed25519 AAAArealkey\n"},
    )

    assert make_syncer(env).run() == 0

    repo_text = (env.dotfiles / ".gitconfig").read_text()
    assert "signingkey = (redacted)" in repo_text
    assert "AAAArealkey" not in repo_text
    # the home file is never scrubbed
    assert (
        "signingkey = ssh-ed25519 AAAArealkey" in (env.home / ".gitconfig").read_text()
    )


def test_sync_preserves_other_gitconfig_lines_around_redaction(tmp_path):
    content = (
        "[user]\n    email = me@example.com\n    signingkey = ssh-ed25519 AAAArealkey\n"
        "[commit]\n    gpgsign = true\n"
    )
    env = build_env(
        tmp_path,
        "include: [.gitconfig]\n",
        home_files={".gitconfig": content},
    )

    assert make_syncer(env).run() == 0

    repo_text = (env.dotfiles / ".gitconfig").read_text()
    assert repo_text == (
        "[user]\n    email = me@example.com\n    signingkey = (redacted)\n"
        "[commit]\n    gpgsign = true\n"
    )


def test_sync_idempotent_when_repo_copy_already_redacted(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [.gitconfig]\n",
        home_files={".gitconfig": "[user]\n    signingkey = ssh-ed25519 AAAArealkey\n"},
        repo_files={".gitconfig": "[user]\n    signingkey = (redacted)\n"},
    )
    # a stale mtime would trigger a re-copy if the comparison used mtime
    repo_stat_before = (env.dotfiles / ".gitconfig").stat()

    with caplog.at_level(logging.INFO, logger="sync_dotfiles"):
        exit_code = make_syncer(env).run()

    assert exit_code == 0
    assert "modify: .gitconfig" not in caplog.text
    assert (
        env.dotfiles / ".gitconfig"
    ).stat().st_mtime_ns == repo_stat_before.st_mtime_ns


def test_sync_recopies_when_signingkey_value_changes_in_home(tmp_path):
    env = build_env(
        tmp_path,
        "include: [.gitconfig]\n",
        home_files={".gitconfig": "[user]\n    signingkey = ssh-ed25519 AAAAoldkey\n"},
        repo_files={".gitconfig": "[user]\n    signingkey = (redacted)\n"},
    )
    (env.home / ".gitconfig").write_text(
        "[user]\n    signingkey = ssh-ed25519 AAAAnewkey\n"
    )

    assert make_syncer(env).run() == 0

    repo_text = (env.dotfiles / ".gitconfig").read_text()
    assert repo_text == "[user]\n    signingkey = (redacted)\n"
    assert "AAAAnewkey" not in repo_text


def test_sync_adds_redacted_copy_for_new_gitconfig_without_signingkey(tmp_path):
    env = build_env(
        tmp_path,
        "include: [.gitconfig]\n",
        home_files={".gitconfig": "[user]\n    name = Cam\n"},
    )

    assert make_syncer(env).run() == 0

    assert (env.dotfiles / ".gitconfig").read_text() == "[user]\n    name = Cam\n"


def test_scrub_rules_only_apply_to_their_own_paths(tmp_path):
    env = build_env(
        tmp_path,
        "include: [.gitconfig, other.conf]\n",
        home_files={
            ".gitconfig": "[user]\n    signingkey = ssh-ed25519 AAAArealkey\n",
            "other.conf": "signingkey = ssh-ed25519 AAAArealkey\n",
        },
    )

    assert make_syncer(env).run() == 0

    assert "signingkey = (redacted)" in (env.dotfiles / ".gitconfig").read_text()
    assert (env.dotfiles / "other.conf").read_text() == (
        "signingkey = ssh-ed25519 AAAArealkey\n"
    )


def test_dry_run_reports_redaction_plan_without_mutating_anything(tmp_path):
    env = build_env(
        tmp_path,
        "include: [.gitconfig]\n",
        home_files={".gitconfig": "[user]\n    signingkey = ssh-ed25519 AAAArealkey\n"},
        repo_files={".gitconfig": "[user]\n    signingkey = ssh-ed25519 AAAAoldkey\n"},
    )
    before_home = snapshot(env.home)
    before_repo = snapshot(env.dotfiles)

    exit_code = make_syncer(env, dry_run=True).run()

    assert exit_code == 2
    assert snapshot(env.home) == before_home
    assert snapshot(env.dotfiles) == before_repo
