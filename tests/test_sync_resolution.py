"""Tests for manifest-driven managed-set resolution in sync_dotfiles."""

import logging
import os

import pytest
from conftest import build_env, make_syncer, managed_keys


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


@pytest.mark.parametrize(
    "anchor",
    ["'^pulse$'", "'pulse'"],
    ids=["anchored-nested", "unanchored-nested"],
)
def test_nested_exclude_anchoring_variants_prune_within_scope(tmp_path, anchor):
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


def test_recursive_glob_skips_children_pruned_by_exclude(tmp_path):
    env = build_env(
        tmp_path,
        "include: ['tools/**/*.lua']\nexclude: ['^tools/skip$']\n",
        home_files={"tools/keep/a.lua": "a", "tools/skip/b.lua": "b"},
    )

    assert managed_keys(make_syncer(env)) == ["tools/keep/a.lua"]


def test_single_level_glob_skips_children_pruned_by_exclude(tmp_path):
    env = build_env(
        tmp_path,
        "include: ['.config/*/x.conf']\nexclude: ['^\\.config/skip$']\n",
        home_files={".config/keep/x.conf": "k", ".config/skip/x.conf": "s"},
    )

    assert managed_keys(make_syncer(env)) == [".config/keep/x.conf"]


def test_literal_glob_component_pruned_by_exclude_stops_the_walk(tmp_path):
    env = build_env(
        tmp_path,
        "include: ['tools/*/sub/x.conf']\nexclude: ['^tools/a/sub$']\n",
        home_files={"tools/a/sub/x.conf": "a", "tools/b/sub/x.conf": "b"},
    )

    assert managed_keys(make_syncer(env)) == ["tools/b/sub/x.conf"]


def test_non_regular_file_entry_is_an_error(tmp_path):
    env = build_env(tmp_path, "include: [pipe]\n", home_files={"keep.txt": "k"})
    os.mkfifo(env.home / "pipe")
    assessment = make_syncer(env).assessment()

    assert any("pipe: not a regular file" in m for m in assessment.errors)


def test_non_regular_file_inside_a_walked_dir_is_an_error(tmp_path):
    env = build_env(tmp_path, "include: [tool]\n", home_files={"tool/a.conf": "a"})
    os.mkfifo(env.home / "tool/pipe")
    syncer = make_syncer(env)
    assessment = syncer.assessment()

    assert managed_keys(syncer) == ["tool/a.conf"]
    assert any("tool/pipe: not a regular file" in m for m in assessment.errors)


def test_duplicate_include_keeps_the_first_entry(tmp_path, caplog):
    env = build_env(
        tmp_path,
        "include:\n  - .config\n  - .config/x.conf\n",
        home_files={".config/x.conf": "x"},
    )

    with caplog.at_level(logging.DEBUG, logger="sync_dotfiles"):
        managed = managed_keys(make_syncer(env))

    assert managed == [".config/x.conf"]
    assert "Duplicate include for .config/x.conf" in caplog.text


def test_watch_covers_names_matched_by_a_glob_include_item(tmp_path):
    env = build_env(
        tmp_path,
        "include:\n  - path: .config\n    include: ['*.conf']\n",
        home_files={".config/a.conf": "a", ".config/other/b": "b"},
    )
    assessment = make_syncer(env).assessment()

    assert [candidate.rel.as_posix() for candidate in assessment.watch] == [
        ".config/other"
    ]


def test_repo_file_only_reachable_by_a_glob_is_an_orphan(tmp_path):
    env = build_env(
        tmp_path,
        "include: ['.config/*/x.conf']\n",
        home_files={".config/a/x.conf": "x"},
        repo_files={".config/a/x.conf": "x", ".config/z/other.conf": "o"},
    )
    assessment = make_syncer(env).assessment()

    assert [rel.as_posix() for rel in assessment.orphans] == [".config/z/other.conf"]


def test_allow_orphan_in_an_exclude_only_nested_scope_keeps_repo_files(tmp_path):
    env = build_env(
        tmp_path,
        (
            "include:\n"
            "  - path: tool\n"
            "    exclude:\n"
            "      - pattern: '^cache$'\n"
            "        allow_orphan: true\n"
        ),
        home_files={"tool/a.conf": "a"},
        repo_files={"tool/a.conf": "a", "tool/cache/blob": "b"},
    )
    assessment = make_syncer(env).assessment()

    assert assessment.orphans == ()
    assert [rel.as_posix() for rel in assessment.allowed_orphans] == ["tool/cache/blob"]


def test_repo_copy_of_a_symlinked_file_inside_a_dir_entry_is_skipped(tmp_path):
    env = build_env(
        tmp_path,
        "include: [app]\n",
        home_files={"app/real.txt": "r"},
        repo_files={"app/real.txt": "r", "app/link.txt": "r"},
    )
    (env.home / "app/link.txt").symlink_to(env.home / "app/real.txt")
    assessment = make_syncer(env).assessment()

    assert [rel.as_posix() for rel in assessment.skipped_copies] == ["app/link.txt"]
    assert assessment.stale == ()


def test_missing_repository_directory_is_reported(tmp_path, caplog):
    env = build_env(tmp_path, "include: [f.txt]\n", home_files={"f.txt": "f"})
    env.dotfiles.rmdir()

    with caplog.at_level(logging.ERROR, logger="sync_dotfiles"):
        exit_code = make_syncer(env).status()

    assert exit_code == 1
    assert "repository directory is missing" in caplog.text
