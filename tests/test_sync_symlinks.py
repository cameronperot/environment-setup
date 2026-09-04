"""Tests for symlink handling: skipping, following, loops, and repository copies."""

import logging
import os

from conftest import build_env, make_syncer, managed_keys


def test_glob_mid_path_symlinked_dir_is_skipped_by_default(tmp_path):
    env = build_env(
        tmp_path,
        "include: ['foo/*/bar.conf']\n",
        home_files={"real/bar.conf": "b"},
    )
    (env.home / "foo").mkdir()
    (env.home / "foo/link").symlink_to(env.home / "real")
    syncer = make_syncer(env)
    assessment = syncer.assessment()

    assert managed_keys(syncer) == []
    assert [rel.as_posix() for rel in assessment.symlink_skips] == ["foo/link"]


def test_glob_mid_path_symlinked_dir_is_followed_under_opt_in(tmp_path):
    env = build_env(
        tmp_path,
        "include: ['foo/*/bar.conf']\n",
        home_files={"real/bar.conf": "b"},
    )
    (env.home / "foo").mkdir()
    (env.home / "foo/link").symlink_to(env.home / "real")
    syncer = make_syncer(env, follow_symlinks=True)

    assert managed_keys(syncer) == ["foo/link/bar.conf"]
    assert syncer.assessment().symlink_skips == ()


def test_recursive_glob_does_not_traverse_symlinked_dirs_by_default(tmp_path):
    env = build_env(
        tmp_path,
        "include: ['foo/**/bar.conf']\n",
        home_files={"real/bar.conf": "b"},
    )
    (env.home / "foo").mkdir()
    (env.home / "foo/link").symlink_to(env.home / "real")
    syncer = make_syncer(env)
    assessment = syncer.assessment()

    assert managed_keys(syncer) == []
    assert [rel.as_posix() for rel in assessment.symlink_skips] == ["foo/link"]


def test_symlink_skipped_by_default(tmp_path):
    env = build_env(
        tmp_path,
        "include: [link.txt]\n",
        home_files={"real.txt": "content"},
    )
    (env.home / "link.txt").symlink_to(env.home / "real.txt")
    assessment = make_syncer(env).assessment()

    assert managed_keys(make_syncer(env)) == []
    assert [rel.as_posix() for rel in assessment.symlink_skips] == ["link.txt"]
    assert assessment.errors == ()


def test_repo_copy_of_symlinked_file_entry_is_kept_not_orphaned(tmp_path):
    env = build_env(
        tmp_path,
        "include: [link.txt]\n",
        home_files={"real.txt": "content"},
        repo_files={"link.txt": "old copy"},
    )
    (env.home / "link.txt").symlink_to(env.home / "real.txt")
    assessment = make_syncer(env).assessment()

    assert assessment.orphans == ()
    assert [rel.as_posix() for rel in assessment.skipped_copies] == ["link.txt"]


def test_repo_copies_under_symlinked_dir_entry_are_kept_not_stale(tmp_path):
    env = build_env(
        tmp_path,
        "include: [app]\n",
        home_files={"app-real/settings.conf": "hello"},
        repo_files={"app/settings.conf": "hello"},
    )
    (env.home / "app").symlink_to(env.home / "app-real")
    assessment = make_syncer(env).assessment()

    assert managed_keys(make_syncer(env)) == []
    assert assessment.stale == ()
    assert assessment.orphans == ()
    assert [rel.as_posix() for rel in assessment.skipped_copies] == [
        "app/settings.conf"
    ]


def test_follow_symlinks_syncs_symlinked_dir_entry_normally(tmp_path):
    env = build_env(
        tmp_path,
        "include: [app]\n",
        home_files={"app-real/settings.conf": "hello"},
        repo_files={"app/settings.conf": "hello"},
    )
    (env.home / "app").symlink_to(env.home / "app-real")
    syncer = make_syncer(env, follow_symlinks=True)

    assert managed_keys(syncer) == ["app/settings.conf"]
    assert syncer.assessment().skipped_copies == ()


def test_follow_symlinks_dereferences_into_real_copies(tmp_path):
    env = build_env(
        tmp_path,
        "include: [link.txt]\n",
        home_files={"real.txt": "content"},
    )
    (env.home / "link.txt").symlink_to(env.home / "real.txt")
    syncer = make_syncer(env, follow_symlinks=True)

    assert managed_keys(syncer) == ["link.txt"]
    assert syncer.assessment().symlink_skips == ()
    assert syncer.run() == 0
    assert (env.dotfiles / "link.txt").read_text() == "content"


def test_broken_symlink_reported_as_error(tmp_path):
    env = build_env(
        tmp_path,
        "include: [broken]\n",
        home_files={"keep.txt": "k"},
    )
    (env.home / "broken").symlink_to(env.home / "nowhere")
    assessment = make_syncer(env).assessment()

    assert any("broken symlink" in message for message in assessment.errors)


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


def test_broken_symlink_fails_the_run(tmp_path):
    env = build_env(
        tmp_path,
        "include: [broken]\n",
        home_files={"keep.txt": "k"},
    )
    (env.home / "broken").symlink_to(env.home / "nowhere")

    assert make_syncer(env).run() == 1


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


def test_literal_glob_component_that_is_a_symlink_is_skipped_by_default(tmp_path):
    env = build_env(
        tmp_path,
        "include: ['tools/*/link/f.conf']\n",
        home_files={"tools/a/target/f.conf": "f"},
    )
    (env.home / "tools/a/link").symlink_to(env.home / "tools/a/target")
    syncer = make_syncer(env)
    assessment = syncer.assessment()

    assert managed_keys(syncer) == []
    assert [rel.as_posix() for rel in assessment.symlink_skips] == ["tools/a/link"]


def test_broken_mid_path_glob_symlink_is_an_error(tmp_path):
    env = build_env(
        tmp_path,
        "include: ['foo/*/bar.conf']\n",
        home_files={"foo/keep": "k"},
    )
    (env.home / "foo/link").symlink_to(env.home / "nowhere")
    assessment = make_syncer(env).assessment()

    assert any("foo/link: broken symlink" in message for message in assessment.errors)


def test_followed_mid_path_glob_symlink_to_a_file_matches_nothing(tmp_path):
    env = build_env(
        tmp_path,
        "include: ['foo/*/bar.conf']\n",
        home_files={"real.txt": "r", "foo/keep": "k"},
    )
    (env.home / "foo/link").symlink_to(env.home / "real.txt")
    syncer = make_syncer(env, follow_symlinks=True)

    assert managed_keys(syncer) == []
    assert syncer.assessment().errors == ()


def test_glob_symlink_loop_is_skipped_with_a_warning(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: ['real/**/bar.conf']\n",
        home_files={"real/bar.conf": "b"},
    )
    (env.home / "real/self").symlink_to(env.home / "real")

    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        managed = managed_keys(make_syncer(env, follow_symlinks=True))

    # following the link once is legitimate; the second encounter is the loop
    assert managed == ["real/bar.conf", "real/self/bar.conf"]
    assert "Symlink loop skipped: real/self/self" in caplog.text


def test_glob_terminal_match_that_is_a_symlink_is_skipped(tmp_path):
    env = build_env(
        tmp_path,
        "include: ['tools/*']\n",
        home_files={"tools/real.txt": "r"},
    )
    (env.home / "tools/link").symlink_to(env.home / "tools/real.txt")
    syncer = make_syncer(env)
    assessment = syncer.assessment()

    assert managed_keys(syncer) == ["tools/real.txt"]
    assert [rel.as_posix() for rel in assessment.symlink_skips] == ["tools/link"]


def test_glob_terminal_match_that_is_not_a_regular_file_is_an_error(tmp_path):
    env = build_env(
        tmp_path,
        "include: ['tools/*']\n",
        home_files={"tools/real.txt": "r"},
    )
    os.mkfifo(env.home / "tools/pipe")
    assessment = make_syncer(env).assessment()

    assert any("tools/pipe: not a regular file" in m for m in assessment.errors)


def test_followed_symlink_to_a_non_regular_file_is_an_error(tmp_path):
    env = build_env(
        tmp_path,
        "include: [link]\n",
        home_files={"keep.txt": "k"},
    )
    os.mkfifo(env.home / "target")
    (env.home / "link").symlink_to(env.home / "target")
    assessment = make_syncer(env, follow_symlinks=True).assessment()

    assert any(
        "link: symlink target is not a regular file" in m for m in assessment.errors
    )
