"""Tests for manifest-driven managed-set resolution in sync_dotfiles."""

import logging

import pytest
from conftest import build_env, make_syncer
from sync_dotfiles import ConfigError, Manifest


def managed_keys(syncer):
    """Run a resolution and return the sorted managed home-relative paths.

    Args:
        syncer: The engine to resolve with.

    Returns:
        Sorted home-relative POSIX paths of managed files.
    """
    return sorted(syncer.assessment().managed)


def test_whole_dir_include_walks_entire_tree(tmp_path):
    env = build_env(
        tmp_path,
        "include: [tool]\n",
        home_files={"tool/a.conf": "a", "tool/sub/b.conf": "b"},
        repo_files={"tool/a.conf": "a", "tool/sub/b.conf": "b"},
    )

    assert managed_keys(make_syncer(env)) == ["tool/a.conf", "tool/sub/b.conf"]


def test_top_level_non_dot_entries_are_never_walked(tmp_path):
    env = build_env(
        tmp_path,
        "include: [.zshrc]\n",
        home_files={".zshrc": "zsh", "regular/x.txt": "x"},
        repo_files={".zshrc": "zsh"},
    )

    assert managed_keys(make_syncer(env)) == [".zshrc"]


def test_curated_nested_include_flags_unexpected_repo_files_as_orphans(tmp_path):
    env = build_env(
        tmp_path,
        "include:\n  - path: .config\n    include: [tool/a.conf]\n",
        home_files={".config/tool/a.conf": "a", ".config/tool/unexpected.conf": "u"},
        repo_files={".config/tool/a.conf": "a", ".config/tool/unexpected.conf": "u"},
    )
    assessment = make_syncer(env).assessment()

    assert managed_keys(make_syncer(env)) == [".config/tool/a.conf"]
    assert [rel.as_posix() for rel in assessment.orphans] == [
        ".config/tool/unexpected.conf"
    ]


def test_scope_with_include_and_exclude_prunes_within_selection(tmp_path):
    env = build_env(
        tmp_path,
        (
            "include:\n"
            "  - path: .config\n"
            "    include:\n"
            "      - path: proj\n"
            "        include: [src]\n"
            "        exclude: ['secret\\.txt$']\n"
        ),
        home_files={
            ".config/proj/src/main.py": "m",
            ".config/proj/src/secret.txt": "s",
        },
        repo_files={
            ".config/proj/src/main.py": "m",
            ".config/proj/src/secret.txt": "s",
        },
    )
    assessment = make_syncer(env).assessment()

    assert managed_keys(make_syncer(env)) == [".config/proj/src/main.py"]
    assert [rel.as_posix() for rel in assessment.orphans] == [
        ".config/proj/src/secret.txt"
    ]


def test_anchored_root_exclude_matches_top_level_entry_only(tmp_path):
    env = build_env(
        tmp_path,
        "include: [data]\nexclude: ['^\\.cache$']\n",
        home_files={"data/.cache/blob": "b", "data/keep.txt": "k"},
        repo_files={"data/.cache/blob": "b", "data/keep.txt": "k"},
    )
    assessment = make_syncer(env).assessment()

    assert managed_keys(make_syncer(env)) == ["data/.cache/blob", "data/keep.txt"]
    assert assessment.orphans == ()


def test_unanchored_root_exclude_prunes_at_any_depth(tmp_path):
    env = build_env(
        tmp_path,
        "include: [data]\nexclude: ['\\.cache$']\n",
        home_files={"data/.cache/blob": "b", "data/keep.txt": "k"},
        repo_files={"data/.cache/blob": "b", "data/keep.txt": "k"},
    )
    assessment = make_syncer(env).assessment()

    assert managed_keys(make_syncer(env)) == ["data/keep.txt"]
    assert [rel.as_posix() for rel in assessment.orphans] == ["data/.cache/blob"]


def test_root_exclude_prunes_subtree_of_included_dir(tmp_path):
    env = build_env(
        tmp_path,
        "include: [.config]\nexclude: ['^\\.config/pulse$']\n",
        home_files={".config/pulse/x": "x", ".config/other/y": "y"},
        repo_files={".config/pulse/x": "x", ".config/other/y": "y"},
    )
    assessment = make_syncer(env).assessment()

    assert managed_keys(make_syncer(env)) == [".config/other/y"]
    assert [rel.as_posix() for rel in assessment.orphans] == [".config/pulse/x"]


def test_nested_exclude_is_scope_relative_and_leaves_root_paths_alone(tmp_path):
    env = build_env(
        tmp_path,
        ("include:\n  - pulse\n  - path: .config\n    exclude: ['^pulse$']\n"),
        home_files={"pulse/x": "x", ".config/pulse/y": "y"},
        repo_files={"pulse/x": "x", ".config/pulse/y": "y"},
    )
    assessment = make_syncer(env).assessment()

    assert managed_keys(make_syncer(env)) == ["pulse/x"]
    assert [rel.as_posix() for rel in assessment.orphans] == [".config/pulse/y"]


def test_whole_home_include_with_non_dot_exclude_keeps_only_dot_paths(tmp_path):
    env = build_env(
        tmp_path,
        "include: [path: .]\nexclude: ['^[^.]']\n",
        home_files={".zshrc": "zsh", ".config/tool/x.conf": "x", "regular/y": "y"},
        repo_files={".zshrc": "zsh", ".config/tool/x.conf": "x"},
    )
    assessment = make_syncer(env).assessment()

    assert managed_keys(make_syncer(env)) == [".config/tool/x.conf", ".zshrc"]
    assert assessment.orphans == ()


def test_glob_expansion_selects_single_level_matches(tmp_path):
    env = build_env(
        tmp_path,
        "include: ['.config/*/*.conf']\n",
        home_files={
            ".config/a/x.conf": "x",
            ".config/b/y.conf": "y",
            ".config/c/deep/z.conf": "z",
        },
    )

    assert managed_keys(make_syncer(env)) == [".config/a/x.conf", ".config/b/y.conf"]


def test_recursive_glob_expansion_covers_nested_matches(tmp_path):
    env = build_env(
        tmp_path,
        "include: ['tools/**/*.lua']\n",
        home_files={
            "tools/a.lua": "a",
            "tools/sub/b.lua": "b",
            "tools/sub/deep/c.lua": "c",
            "tools/readme.txt": "r",
        },
    )

    assert managed_keys(make_syncer(env)) == [
        "tools/a.lua",
        "tools/sub/b.lua",
        "tools/sub/deep/c.lua",
    ]


def test_glob_matching_directory_includes_it_wholly(tmp_path):
    env = build_env(
        tmp_path,
        "include: ['tools/*']\n",
        home_files={"tools/a/b.conf": "b", "tools/c.txt": "c", "tools/d/e.lua": "e"},
    )

    assert managed_keys(make_syncer(env)) == [
        "tools/a/b.conf",
        "tools/c.txt",
        "tools/d/e.lua",
    ]


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


def test_unused_exclude_pattern_logs_warning(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include: [data]\nexclude: ['never-matches']\n",
        home_files={"data/x": "x"},
    )

    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        make_syncer(env).status()

    assert "Unused exclude pattern(s): 'never-matches'" in caplog.text


def test_optional_exclude_matching_nothing_stays_silent(tmp_path, caplog):
    env = build_env(
        tmp_path,
        (
            "include: [data]\n"
            "exclude:\n"
            "  - pattern: 'never-matches'\n"
            "    optional: true\n"
        ),
        home_files={"data/x": "x"},
    )

    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        make_syncer(env).status()

    assert "Unused exclude pattern" not in caplog.text


def test_newly_excluded_repo_file_becomes_orphan(tmp_path):
    env = build_env(
        tmp_path,
        ("include:\n  - path: tool\n    exclude: ['logs\\.db$']\n"),
        home_files={"tool/data.txt": "d"},
        repo_files={"tool/data.txt": "d", "tool/logs.db": "log"},
    )
    assessment = make_syncer(env).assessment()

    assert managed_keys(make_syncer(env)) == ["tool/data.txt"]
    assert [rel.as_posix() for rel in assessment.orphans] == ["tool/logs.db"]


def test_whole_missing_entry_reports_and_collects_repo_copies(tmp_path):
    env = build_env(
        tmp_path,
        "include: [gone]\n",
        home_files={"here.txt": "h"},
        repo_files={"gone/f": "f"},
    )
    assessment = make_syncer(env).assessment()

    assert [
        (entry.rel.as_posix(), entry.optional) for entry in assessment.missing_entries
    ] == [("gone", False)]
    assert [copy.rel.as_posix() for copy in assessment.missing_copies] == ["gone/f"]
    assert assessment.missing_copies[0].optional is False


def test_missing_file_within_live_dir_is_stale_not_missing_entry(tmp_path):
    env = build_env(
        tmp_path,
        "include: [live]\n",
        home_files={"live/a.txt": "a"},
        repo_files={"live/a.txt": "a", "live/b.txt": "b"},
    )
    assessment = make_syncer(env).assessment()

    assert assessment.missing_entries == ()
    assert [rel.as_posix() for rel in assessment.stale] == ["live/b.txt"]
    assert assessment.missing_copies == ()


def test_optional_missing_entry_is_exempt_from_warnings_and_prune(tmp_path):
    env = build_env(
        tmp_path,
        "include:\n  - path: gone\n    optional: true\n",
        home_files={"here.txt": "h"},
        repo_files={"gone/f": "f"},
    )
    assessment = make_syncer(env).assessment()

    assert assessment.missing_entries[0].optional is True
    assert assessment.missing_copies[0].optional is True


def test_missing_optional_file_within_curated_dir_is_protected(tmp_path):
    env = build_env(
        tmp_path,
        (
            "include:\n"
            "  - path: tool\n"
            "    include:\n"
            "      - path: '.aider.conf.yml'\n"
            "        optional: true\n"
        ),
        home_files={"tool/other.txt": "o"},
        repo_files={"tool/.aider.conf.yml": "c", "tool/other.txt": "o"},
    )
    assessment = make_syncer(env).assessment()

    assert assessment.stale == ()
    assert [
        (copy.rel.as_posix(), copy.optional) for copy in assessment.missing_copies
    ] == [("tool/.aider.conf.yml", True)]


def test_root_exclude_silences_untracked_watch_candidate(tmp_path):
    env = build_env(
        tmp_path,
        "include: [.tool]\nexclude:\n  - pattern: '^\\.state$'\n    optional: true\n",
        home_files={".tool/x": "x", ".state/cache": "c"},
    )
    assessment = make_syncer(env).assessment()

    assert [c.rel.as_posix() for c in assessment.watch] == []


def test_untracked_watch_reports_uncovered_top_level_dot_entries(tmp_path):
    env = build_env(
        tmp_path,
        "include: [.tool]\n",
        home_files={".tool/x": "x", ".newtool/conf": "c"},
    )
    assessment = make_syncer(env).assessment()

    assert [(c.rel.as_posix(), c.scope) for c in assessment.watch] == [
        (".newtool", "home")
    ]


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


@pytest.mark.parametrize(
    ("anchor", "expected_managed"),
    [
        ("'^pulse$'", []),
        ("'pulse'", []),
    ],
    ids=["anchored-nested", "unanchored-nested"],
)
def test_nested_exclude_anchoring_variants_prune_within_scope(
    tmp_path, anchor, expected_managed
):
    env = build_env(
        tmp_path,
        f"include:\n  - path: .config\n    exclude: [{anchor}]\n",
        home_files={".config/pulse/x": "x", ".config/keep/y": "y"},
    )

    assert managed_keys(make_syncer(env)) == [".config/keep/y"]


def test_same_pattern_in_two_scopes_lints_independently(tmp_path, caplog):
    env = build_env(
        tmp_path,
        (
            "include:\n"
            "  - path: d1\n"
            "    exclude: ['held']\n"
            "  - path: d2\n"
            "    exclude: ['held']\n"
        ),
        home_files={"d1/held": "h", "d1/other": "o", "d2/other": "o"},
    )

    with caplog.at_level(logging.WARNING, logger="sync_dotfiles"):
        make_syncer(env).status()

    assert "Unused exclude pattern(s): 'held'" in caplog.text


def test_exclude_allow_orphan_flag_parses(tmp_path):
    env = build_env(
        tmp_path,
        (
            "include: [f.txt]\n"
            "exclude:\n"
            "  - 'plain'\n"
            "  - pattern: 'mapped'\n"
            "  - pattern: 'kept'\n"
            "    allow_orphan: true\n"
        ),
        home_files={"f.txt": "f"},
    )
    excludes = env.manifest.root.exclude

    assert [exclude.allow_orphan for exclude in excludes] == [False, False, True]


def test_exclude_allow_orphan_must_be_boolean(tmp_path):
    config = tmp_path / "dotfiles.yaml"
    config.write_text(
        "include: [f.txt]\nexclude:\n  - pattern: 'x'\n    allow_orphan: 'yes'\n"
    )

    with pytest.raises(ConfigError, match="'allow_orphan' must be a boolean"):
        Manifest.load(config)


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
        (
            "include:\n"
            "  - path: tool\n"
            "    include: [a.conf]\n"
            "    exclude: ['^cache$']\n"
        ),
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
