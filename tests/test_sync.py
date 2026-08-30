"""Tests for sync planning, execution, pruning, and dry runs."""

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


def test_sync_keeps_repo_copies_under_symlinked_dir_entry(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [app]\n",
        home_files={"app-real/settings.conf": "hello"},
        repo_files={"app/settings.conf": "hello"},
    )
    (env.home / "app").symlink_to(env.home / "app-real")

    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        exit_code = make_syncer(env).run()

    assert exit_code == 0
    assert (env.dotfiles / "app/settings.conf").exists()
    assert "Repo copy kept" in caplog.text


def test_prune_keeps_repo_copies_of_symlinked_entries(tmp_path):
    env = build_env(
        tmp_path,
        "include: [link.txt]\n",
        home_files={"real.txt": "content"},
        repo_files={"link.txt": "old copy"},
    )
    (env.home / "link.txt").symlink_to(env.home / "real.txt")

    assert make_syncer(env, prune=True).run() == 0

    assert (env.dotfiles / "link.txt").exists()


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


def test_broken_symlink_fails_the_run(tmp_path):
    env = build_env(
        tmp_path,
        "include: [broken]\n",
        home_files={"keep.txt": "k"},
    )
    (env.home / "broken").symlink_to(env.home / "nowhere")

    assert make_syncer(env).run() == 1


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


def test_distinct_symlinks_to_same_dir_both_sync(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [.x, .y]\n",
        home_files={"realdir/f1.txt": "1", "realdir/f2.txt": "2"},
        repo_files={".x/f1.txt": "1", ".y/f2.txt": "2"},
    )
    (env.home / ".x").symlink_to(env.home / "realdir")
    (env.home / ".y").symlink_to(env.home / "realdir")

    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        exit_code = make_syncer(env, follow_symlinks=True).run()

    assert exit_code == 0
    assert "Symlink loop skipped" not in caplog.text
    assert (env.dotfiles / ".x/f1.txt").read_text() == "1"
    assert (env.dotfiles / ".y/f2.txt").read_text() == "2"


def test_symlink_loop_skips_walk_and_keeps_repo_copies(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [app]\n",
        home_files={"app-real/settings.conf": "hello"},
        repo_files={"app/settings.conf": "hello", "app/sub/x.txt": "x"},
    )
    (env.home / "app").symlink_to(env.home / "app-real")
    (env.home / "app-real/sub").symlink_to(env.home / "app-real")

    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        exit_code = make_syncer(env, follow_symlinks=True).run()

    assert exit_code == 0
    assert "Symlink loop skipped" in caplog.text
    assert (env.dotfiles / "app/sub/x.txt").read_text() == "x"


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
