"""Tests for the CLI modes, exit codes, the untracked watch, and orphan reporting."""

import logging
import os

import pytest
from conftest import build_env, make_syncer, managed_keys, snapshot

import sync_dotfiles
from sync_dotfiles import main, parse_args


@pytest.fixture(autouse=True)
def unbind_real_home(monkeypatch, tmp_path):
    """Point the module-level CLI directories at nothing, so a forgotten bind cannot
    sync the real ``$HOME`` into the working tree.

    Args:
        monkeypatch: The pytest monkeypatch fixture.
        tmp_path: Pytest temporary directory root.
    """
    monkeypatch.setattr(sync_dotfiles, "HOME_DIR", tmp_path / "absent-home")
    monkeypatch.setattr(sync_dotfiles, "DOTFILES_DIR", tmp_path / "absent-dotfiles")


def bind_cli_dirs(monkeypatch, env):
    """Bind ``main``'s module-level directories to a fixture environment.

    Args:
        monkeypatch: The pytest monkeypatch fixture.
        env: The fixture environment to bind to.
    """
    monkeypatch.setattr(sync_dotfiles, "HOME_DIR", env.home)
    monkeypatch.setattr(sync_dotfiles, "DOTFILES_DIR", env.dotfiles)


def cli_env(tmp_path):
    """Build an environment with one pending change and one clean file.

    Args:
        tmp_path: Pytest temporary directory root.

    Returns:
        The fixture environment.
    """
    return build_env(
        tmp_path,
        "include: [live]\n",
        home_files={"live/a.txt": "a", "live/new.txt": "n"},
        repo_files={"live/a.txt": "a"},
    )


def test_main_status_reports_and_exits_zero(tmp_path, monkeypatch, caplog):
    env = cli_env(tmp_path)
    bind_cli_dirs(monkeypatch, env)

    with caplog.at_level(logging.INFO, logger="sync_dotfiles"):
        exit_code = main(["--status", "--config", str(env.config)])

    assert exit_code == 0
    assert "add: live/new.txt" in caplog.text
    assert not (env.dotfiles / "live/new.txt").exists()


def test_main_check_exits_two_when_changes_are_pending(tmp_path, monkeypatch):
    env = cli_env(tmp_path)
    bind_cli_dirs(monkeypatch, env)

    assert main(["--check", "--config", str(env.config)]) == 2


def test_main_discover_exits_zero(tmp_path, monkeypatch, caplog):
    env = cli_env(tmp_path)
    (env.home / ".untracked").mkdir()
    (env.home / ".untracked/x").write_text("x")
    bind_cli_dirs(monkeypatch, env)

    with caplog.at_level(logging.INFO, logger="sync_dotfiles"):
        exit_code = main(["--discover", "--config", str(env.config)])

    assert exit_code == 0
    assert "Untracked candidates: 1" in caplog.text


def test_main_syncs_and_exits_zero(tmp_path, monkeypatch):
    env = cli_env(tmp_path)
    bind_cli_dirs(monkeypatch, env)

    assert main(["--config", str(env.config)]) == 0
    assert (env.dotfiles / "live/new.txt").read_text() == "n"


def test_main_dry_run_exits_two_without_writing(tmp_path, monkeypatch):
    env = cli_env(tmp_path)
    bind_cli_dirs(monkeypatch, env)

    assert main(["--dry-run", "--config", str(env.config)]) == 2
    assert not (env.dotfiles / "live/new.txt").exists()


def test_main_warns_that_stage_is_ignored_by_report_only_modes(
    tmp_path, monkeypatch, caplog
):
    env = cli_env(tmp_path)
    bind_cli_dirs(monkeypatch, env)

    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        main(["--status", "--stage", "--config", str(env.config)])

    assert "--stage has no effect with report-only modes" in caplog.text


def test_main_warns_that_stage_is_ignored_by_dry_run(tmp_path, monkeypatch, caplog):
    env = cli_env(tmp_path)
    bind_cli_dirs(monkeypatch, env)

    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        main(["--dry-run", "--stage", "--config", str(env.config)])

    assert "--stage has no effect with --dry-run" in caplog.text


def test_main_reports_an_unloadable_manifest_and_exits_one(tmp_path, caplog):
    # no bind needed: main returns before it builds a syncer
    with caplog.at_level(logging.ERROR, logger="sync_dotfiles"):
        exit_code = main(["--config", str(tmp_path / "absent.yaml")])

    assert exit_code == 1
    assert "cannot read manifest" in caplog.text


def test_main_verbose_enables_debug_logging(tmp_path, monkeypatch):
    env = cli_env(tmp_path)
    bind_cli_dirs(monkeypatch, env)

    assert main(["--verbose", "--config", str(env.config)]) == 0


def test_main_quiet_restricts_logging(tmp_path, monkeypatch):
    env = cli_env(tmp_path)
    bind_cli_dirs(monkeypatch, env)

    assert main(["--quiet", "--config", str(env.config)]) == 0


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


def test_status_reports_without_syncing(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [live]\n",
        home_files={"live/a.txt": "a", "live/new.txt": "n"},
        repo_files={"live/a.txt": "a", "live/stale.txt": "s"},
    )
    before_home = snapshot(env.home)
    before_repo = snapshot(env.dotfiles)

    with caplog.at_level(logging.INFO, logger="sync_dotfiles"):
        exit_code = make_syncer(env).status()

    assert exit_code == 0
    assert snapshot(env.home) == before_home
    assert snapshot(env.dotfiles) == before_repo
    assert "add: live/new.txt" in caplog.text
    assert "Orphaned repo file" not in caplog.text


def test_allow_orphan_exclude_keeps_repo_files_silent(tmp_path, caplog):
    env = build_env(
        tmp_path,
        (
            "include:\n"
            "  - path: tool\n"
            "    include: [a.conf]\n"
            "    exclude:\n"
            "      - pattern: '^cache$'\n"
            "        allow_orphan: true\n"
        ),
        home_files={"tool/a.conf": "a", "tool/cache/blob": "b"},
        repo_files={"tool/a.conf": "a", "tool/cache/blob/deep": "d"},
    )
    syncer = make_syncer(env)
    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        assert syncer.status() == 0
    assessment = syncer.assessment()

    assert managed_keys(syncer) == ["tool/a.conf"]
    assert [rel.as_posix() for rel in assessment.allowed_orphans] == [
        "tool/cache/blob/deep",
    ]
    assert assessment.orphans == ()
    assert "Orphaned repo file" not in caplog.text


def test_root_allow_orphan_exclude_keeps_untracked_repo_tree(tmp_path):
    env = build_env(
        tmp_path,
        (
            "include: [.zshrc]\n"
            "exclude:\n"
            "  - pattern: '^\\.plannotator$'\n"
            "    optional: true\n"
            "    allow_orphan: true\n"
        ),
        home_files={".zshrc": "zsh"},
        repo_files={".zshrc": "zsh", ".plannotator/history/run.jsonl": "r"},
    )
    assessment = make_syncer(env).assessment()

    assert [rel.as_posix() for rel in assessment.allowed_orphans] == [
        ".plannotator/history/run.jsonl"
    ]
    assert assessment.orphans == ()


def test_plain_exclude_repo_file_remains_orphan(tmp_path):
    env = build_env(
        tmp_path,
        ("include:\n  - path: tool\n    include: [a.conf]\n    exclude: ['^cache$']\n"),
        home_files={"tool/a.conf": "a"},
        repo_files={"tool/cache/blob": "b"},
    )
    assessment = make_syncer(env).assessment()

    assert assessment.allowed_orphans == ()
    assert [rel.as_posix() for rel in assessment.orphans] == ["tool/cache/blob"]


def test_unused_allow_orphan_pattern_still_warns_unless_optional(tmp_path, caplog):
    plain = build_env(
        tmp_path / "plain",
        (
            "include: [f.txt]\n"
            "exclude:\n"
            "  - pattern: '^never$'\n"
            "    allow_orphan: true\n"
        ),
        home_files={"f.txt": "f"},
    )
    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        make_syncer(plain).status()
    assert "Unused exclude pattern(s): '^never$'" in caplog.text

    caplog.clear()
    optional = build_env(
        tmp_path / "optional",
        (
            "include: [f.txt]\n"
            "exclude:\n"
            "  - pattern: '^never$'\n"
            "    optional: true\n"
            "    allow_orphan: true\n"
        ),
        home_files={"f.txt": "f"},
    )
    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        make_syncer(optional).status()
    assert "Unused exclude pattern" not in caplog.text
