"""Tests for the secret guard's detection and enforcement behavior."""

import logging
from pathlib import Path

from conftest import build_env, make_syncer, snapshot

PRIVATE_KEY = (
    "-----BEGIN OPENSSH PRIVATE KEY-----\n"
    "b3BlbnNzaC1rZXktdjEAAAAABGxvY2FsaG9zdAAAAAAAAAAA\n"
    "-----END OPENSSH PRIVATE KEY-----\n"
)


def deny_read(monkeypatch, target):
    """Make ``Path.read_text`` raise ``PermissionError`` for one path only.

    Args:
        monkeypatch: The pytest monkeypatch fixture.
        target: The path whose reads should fail.
    """
    real_read_text = Path.read_text

    def read_text(self, *args, **kwargs):
        if self == target:
            raise PermissionError(13, "Permission denied")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)


def test_private_key_file_is_skipped_with_warning(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [creds.txt]\n",
        home_files={"creds.txt": PRIVATE_KEY},
    )

    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        exit_code = make_syncer(env).run()

    assert exit_code == 0
    assert not (env.dotfiles / "creds.txt").exists()
    assert "possible secret (private key block)" in caplog.text


def test_skipped_secret_warns_exactly_once(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [creds.txt]\n",
        home_files={"creds.txt": PRIVATE_KEY},
    )

    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        make_syncer(env).run()

    secret_warnings = [
        record for record in caplog.records if "possible secret" in record.message
    ]
    assert len(secret_warnings) == 1


def test_strict_secrets_aborts_without_applying_changes(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [creds.txt, other.txt]\n",
        home_files={"creds.txt": PRIVATE_KEY, "other.txt": "clean"},
    )
    before_repo = snapshot(env.dotfiles)

    with caplog.at_level(logging.ERROR, logger="sync_dotfiles"):
        exit_code = make_syncer(env, strict_secrets=True).run()

    assert exit_code == 1
    assert snapshot(env.dotfiles) == before_repo
    assert "creds.txt: possible secret" in caplog.text


def test_manifest_secret_pattern_triggers_skip(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [app.conf]\nsecret_patterns: ['SUPERSECRET\\s*=']\n",
        home_files={"app.conf": "SUPERSECRET=abc123\n"},
    )

    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        exit_code = make_syncer(env).run()

    assert exit_code == 0
    assert not (env.dotfiles / "app.conf").exists()
    assert "possible secret (manifest pattern)" in caplog.text


def test_quoted_credential_assignment_is_flagged(tmp_path):
    env = build_env(
        tmp_path,
        "include: [settings.sh]\n",
        home_files={"settings.sh": 'password = "super-secret-value-123"\n'},
    )

    assert make_syncer(env).run() == 0
    assert not (env.dotfiles / "settings.sh").exists()


def test_env_var_pass_through_is_not_flagged(tmp_path):
    env = build_env(
        tmp_path,
        "include: [aliases.sh]\n",
        home_files={"aliases.sh": 'export API_KEY="${API_KEY}"\n'},
    )

    assert make_syncer(env).run() == 0
    assert (env.dotfiles / "aliases.sh").read_text() == 'export API_KEY="${API_KEY}"\n'


def test_clean_file_syncs_normally_past_the_guard(tmp_path):
    env = build_env(
        tmp_path,
        "include: [settings.conf]\n",
        home_files={"settings.conf": "export EDITOR=nvim\nalias ll='ls -la'\n"},
    )

    assert make_syncer(env).run() == 0
    assert (env.dotfiles / "settings.conf").exists()


def test_unreadable_file_is_reported_as_error_and_not_synced(
    tmp_path, caplog, monkeypatch
):
    env = build_env(
        tmp_path,
        "include: [creds.txt]\n",
        home_files={"creds.txt": "clean"},
    )
    # mode bits cannot express this: root reads a 0o000 file regardless
    deny_read(monkeypatch, env.home / "creds.txt")

    with caplog.at_level(logging.ERROR, logger="sync_dotfiles"):
        exit_code = make_syncer(env).run()

    assert exit_code == 1
    assert not (env.dotfiles / "creds.txt").exists()
    assert "cannot read file for secret scan" in caplog.text


def test_secret_findings_are_deduplicated(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [mixed.txt]\n",
        home_files={
            "mixed.txt": 'token = "abcdefghijklmnop"\ntoken2 = abcdefghijklmnopqrstuv\n'
        },
    )

    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        make_syncer(env).run()

    assert "credential assignment, credential assignment" not in caplog.text
    assert "possible secret (credential assignment)" in caplog.text


def test_binary_file_carries_no_text_signatures_and_syncs(tmp_path, caplog):
    env = build_env(tmp_path, "include: [blob.bin]\n", home_files={"blob.bin": "seed"})
    payload = b"\x80\x81password = hunter2hunter2"
    (env.home / "blob.bin").write_bytes(payload)

    with caplog.at_level(logging.DEBUG, logger="sync_dotfiles"):
        exit_code = make_syncer(env).run()

    assert exit_code == 0
    assert (env.dotfiles / "blob.bin").read_bytes() == payload
    assert "not readable as text" in caplog.text
