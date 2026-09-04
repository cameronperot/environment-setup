"""Tests for sync planning and execution: copies, mirror deletes, and prune."""

import logging
import os

from conftest import build_env, make_syncer, snapshot


def test_sync_copies_only_changed_files_and_preserves_modes(tmp_path):
    env = build_env(
        tmp_path,
        "include: [same.txt, changed.txt, added.txt]\n",
        home_files={"same.txt": "same", "changed.txt": "new", "added.txt": "brand new"},
        repo_files={"same.txt": "same", "changed.txt": "old"},
    )
    for name in ("same.txt", "changed.txt"):
        os.utime(env.home / name, ns=(1000, 1000))
        os.utime(env.dotfiles / name, ns=(1000, 1000))
    os.chmod(env.home / "added.txt", 0o755)
    same_mtime_before = (env.dotfiles / "same.txt").stat().st_mtime_ns

    syncer = make_syncer(env)
    assert syncer.run() == 0

    assert (env.dotfiles / "changed.txt").read_text() == "new"
    assert (env.dotfiles / "changed.txt").stat().st_mtime_ns == 1000
    added = env.dotfiles / "added.txt"
    assert added.read_text() == "brand new"
    assert added.stat().st_mode & 0o7777 == 0o755
    # the file that was already in sync is never re-copied
    assert (env.dotfiles / "same.txt").stat().st_mtime_ns == same_mtime_before


def test_dry_run_reports_plan_without_mutating_anything(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [live]\n",
        home_files={"live/a.txt": "a", "live/new.txt": "n"},
        repo_files={"live/a.txt": "CHANGED-SOURCE-WILL-WIN", "live/stale.txt": "s"},
    )
    before_home = snapshot(env.home)
    before_repo = snapshot(env.dotfiles)

    with caplog.at_level(logging.INFO, logger="sync_dotfiles"):
        exit_code = make_syncer(env, dry_run=True).run()

    assert exit_code == 2
    assert snapshot(env.home) == before_home
    assert snapshot(env.dotfiles) == before_repo
    assert "Dry run: no changes were made" in caplog.text
    assert "add: live/new.txt" in caplog.text
    assert "modify: live/a.txt" in caplog.text
    assert "delete: live/stale.txt" in caplog.text


def test_mirror_delete_removes_repo_files_that_vanished_from_home(tmp_path):
    env = build_env(
        tmp_path,
        "include: [live]\n",
        home_files={"live/a.txt": "a"},
        repo_files={"live/a.txt": "a", "live/sub/deep.txt": "d"},
    )

    assert make_syncer(env).run() == 0

    assert not (env.dotfiles / "live/sub/deep.txt").exists()
    assert not (env.dotfiles / "live/sub").exists()
    assert (env.dotfiles / "live/a.txt").exists()


def test_mirror_delete_never_touches_home(tmp_path):
    env = build_env(
        tmp_path,
        "include: [live]\n",
        home_files={"live/a.txt": "a"},
        repo_files={"live/a.txt": "a", "live/stale.txt": "s"},
    )
    before_home = snapshot(env.home)

    make_syncer(env).run()

    assert snapshot(env.home) == before_home


def test_prune_deletes_orphans_and_missing_copies_but_keeps_optional(tmp_path):
    env = build_env(
        tmp_path,
        ("include:\n  - gone\n  - path: optgone\n    optional: true\n  - live\n"),
        home_files={"live/a.txt": "a"},
        repo_files={
            "orphan/x": "x",
            "gone/f": "f",
            "optgone/f": "f",
            "live/a.txt": "a",
        },
    )

    assert make_syncer(env, prune=True).run() == 0

    assert not (env.dotfiles / "orphan/x").exists()
    assert not (env.dotfiles / "gone/f").exists()
    assert (env.dotfiles / "optgone/f").exists()
    assert (env.dotfiles / "live/a.txt").exists()


def test_prune_reports_but_dry_run_keeps_everything(tmp_path):
    env = build_env(
        tmp_path,
        "include: [live]\n",
        home_files={"live/a.txt": "a"},
        repo_files={"orphan/x": "x", "live/a.txt": "a"},
    )
    before_repo = snapshot(env.dotfiles)

    assert make_syncer(env, prune=True, dry_run=True).run() == 2

    assert snapshot(env.dotfiles) == before_repo


def test_file_vanishing_before_planning_is_reported_not_crashed(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [f.txt]\n",
        home_files={"f.txt": "f"},
        repo_files={"f.txt": "different"},
    )
    syncer = make_syncer(env)
    assessment = syncer.assessment()
    (env.home / "f.txt").unlink()

    with caplog.at_level(logging.ERROR, logger="sync_dotfiles"):
        plan = syncer.build_plan(assessment)
        syncer._report(assessment, plan)

    assert plan.copies == ()
    assert "cannot compare with repo copy" in caplog.text


def test_sync_of_clean_state_exits_zero(tmp_path):
    env = build_env(
        tmp_path,
        "include: [f.txt]\n",
        home_files={"f.txt": "f"},
        repo_files={"f.txt": "f"},
    )
    os.utime(env.home / "f.txt", ns=(1000, 1000))
    os.utime(env.dotfiles / "f.txt", ns=(1000, 1000))

    assert make_syncer(env).run() == 0


def test_home_file_replacing_repo_dir_heals_in_one_run(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [X]\n",
        home_files={"X": "homefile"},
        repo_files={"X/f.txt": "repochild"},
    )

    with caplog.at_level(logging.INFO, logger="sync_dotfiles"):
        exit_code = make_syncer(env).run()

    assert exit_code == 0
    assert "type mismatch" not in caplog.text
    assert (env.dotfiles / "X").is_file()
    assert (env.dotfiles / "X").read_text() == "homefile"


def test_home_dir_replacing_repo_file_heals_in_one_run(tmp_path):
    env = build_env(
        tmp_path,
        "include: [X]\n",
        home_files={"X/f.txt": "content"},
        repo_files={"X": "repofile"},
    )

    assert make_syncer(env).run() == 0
    assert (env.dotfiles / "X/f.txt").read_text() == "content"


def test_prune_deletes_plain_orphans_but_never_allowed_ones(tmp_path):
    env = build_env(
        tmp_path,
        (
            "include:\n"
            "  - path: tool\n"
            "    include: [a.conf]\n"
            "    exclude:\n"
            "      - pattern: '^cache$'\n"
            "        allow_orphan: true\n"
            "      - pattern: '^scratch$'\n"
        ),
        home_files={"tool/a.conf": "a"},
        repo_files={
            "tool/a.conf": "a",
            "tool/cache/kept": "k",
            "tool/scratch/gone": "g",
        },
    )
    syncer = make_syncer(env, prune=True)
    plan = syncer.build_plan(syncer.assessment())

    assert [action.rel.as_posix() for action in plan.prune_deletes] == [
        "tool/scratch/gone"
    ]

    syncer.execute(plan)
    assert (env.dotfiles / "tool/cache/kept").exists()
    assert not (env.dotfiles / "tool/scratch").exists()


def test_prune_deletes_repo_symlink_pointing_to_a_directory(tmp_path):
    env = build_env(
        tmp_path,
        "include: [f.txt]\n",
        home_files={"f.txt": "f"},
        repo_files={"f.txt": "f"},
    )
    (env.dotfiles / "sub").mkdir()
    (env.dotfiles / "link").symlink_to(env.dotfiles / "sub")
    os.utime(env.home / "f.txt", ns=(1000, 1000))
    os.utime(env.dotfiles / "f.txt", ns=(1000, 1000))

    assert make_syncer(env, prune=True).run() == 0

    assert not (env.dotfiles / "link").is_symlink()


def test_copy_refuses_to_write_through_symlinked_repo_ancestor(tmp_path, caplog):
    # the repo-side .config symlink is kept (its $HOME counterpart is an
    # unfollowed symlink), while the overlapping deeper entry still manages
    # .config/x through it: the copy must not escape the repository
    env = build_env(
        tmp_path,
        "include:\n  - .config\n  - path: .config/x\n",
        home_files={".config-real/x": "NEW"},
    )
    (env.home / ".config").symlink_to(env.home / ".config-real")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "x").write_text("OLD")
    (env.dotfiles / ".config").symlink_to(outside)

    with caplog.at_level(logging.ERROR, logger="sync_dotfiles"):
        exit_code = make_syncer(env).run()

    assert exit_code == 1
    assert "repository ancestor .config is a symlink" in caplog.text
    assert (outside / "x").read_text() == "OLD"


def test_repo_symlink_in_place_of_a_managed_file_is_an_error(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [f.txt]\n",
        home_files={"f.txt": "f"},
        repo_files={"other.txt": "o"},
    )
    (env.dotfiles / "f.txt").symlink_to(env.dotfiles / "other.txt")

    with caplog.at_level(logging.ERROR, logger="sync_dotfiles"):
        exit_code = make_syncer(env).run()

    assert exit_code == 1
    assert "f.txt: repository path is a symlink" in caplog.text
    assert (env.dotfiles / "f.txt").read_text() == "o"


def test_delete_of_a_repo_directory_is_reported_not_crashed(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [live]\n",
        home_files={"live/a.txt": "a"},
        repo_files={"live/a.txt": "a", "live/stale.txt": "s"},
    )
    syncer = make_syncer(env)
    plan = syncer.build_plan(syncer.assessment())
    # the stale file turns into a directory between planning and execution
    (env.dotfiles / "live/stale.txt").unlink()
    (env.dotfiles / "live/stale.txt").mkdir()

    with caplog.at_level(logging.ERROR, logger="sync_dotfiles"):
        syncer.execute(plan)

    assert "Failed to delete live/stale.txt" in caplog.text
    assert "repository path is a directory" in caplog.text
    assert (env.dotfiles / "live/stale.txt").is_dir()


def test_empty_repo_directory_is_replaced_by_the_home_file(tmp_path):
    env = build_env(
        tmp_path,
        "include: [f.txt]\n",
        home_files={"f.txt": "f"},
    )
    (env.dotfiles / "f.txt").mkdir()

    assert make_syncer(env).run() == 0
    assert (env.dotfiles / "f.txt").read_text() == "f"


def test_repo_directory_kept_alive_by_an_allowed_orphan_fails_the_copy(
    tmp_path, caplog
):
    env = build_env(
        tmp_path,
        "include: [f.txt]\nexclude:\n  - pattern: 'junk$'\n    allow_orphan: true\n",
        home_files={"f.txt": "f"},
        repo_files={"f.txt/junk": "j"},
    )

    with caplog.at_level(logging.ERROR, logger="sync_dotfiles"):
        exit_code = make_syncer(env).run()

    assert exit_code == 1
    assert "Failed to copy f.txt" in caplog.text
    assert (env.dotfiles / "f.txt/junk").read_text() == "j"


def test_mode_only_change_triggers_a_recopy(tmp_path):
    env = build_env(
        tmp_path,
        "include: [f.txt]\n",
        home_files={"f.txt": "same"},
        repo_files={"f.txt": "same"},
    )
    os.utime(env.home / "f.txt", ns=(1000, 1000))
    os.utime(env.dotfiles / "f.txt", ns=(1000, 1000))
    os.chmod(env.home / "f.txt", 0o755)

    assert make_syncer(env).run() == 0
    assert (env.dotfiles / "f.txt").stat().st_mode & 0o7777 == 0o755


def test_mtime_only_change_triggers_a_recopy(tmp_path):
    env = build_env(
        tmp_path,
        "include: [f.txt]\n",
        home_files={"f.txt": "same"},
        repo_files={"f.txt": "same"},
    )
    os.utime(env.home / "f.txt", ns=(2000, 2000))
    os.utime(env.dotfiles / "f.txt", ns=(1000, 1000))

    assert make_syncer(env).run() == 0
    assert (env.dotfiles / "f.txt").stat().st_mtime_ns == 2000


def test_size_only_change_triggers_a_recopy(tmp_path):
    env = build_env(
        tmp_path,
        "include: [f.txt]\n",
        home_files={"f.txt": "longer content"},
        repo_files={"f.txt": "short"},
    )
    os.utime(env.home / "f.txt", ns=(1000, 1000))
    os.utime(env.dotfiles / "f.txt", ns=(1000, 1000))

    assert make_syncer(env).run() == 0
    assert (env.dotfiles / "f.txt").read_text() == "longer content"
