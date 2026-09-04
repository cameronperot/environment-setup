"""Tests for manifest loading and validation in sync_dotfiles."""

import re

import pytest
from conftest import build_env

from sync_dotfiles import DEFAULT_CONFIG_PATH, ConfigError, Manifest

# (id, manifest text, expected message fragment) for every ConfigError the parser raises
INVALID_MANIFESTS = [
    ("empty-file", "", "manifest is empty"),
    ("top-level-list", "- a\n- b\n", "manifest must be a mapping at the top level"),
    ("malformed-yaml", "include: [a]\n bad: {\n", "YAML parse error"),
    ("root-without-include", "exclude: ['x']\n", "missing required 'include' list"),
    ("empty-include", "include: []\n", "'include' must not be empty"),
    ("include-not-a-list", "include: 'x'\n", "'include' must be a list"),
    ("empty-exclude", "include: [a]\nexclude: []\n", "'exclude' must not be empty"),
    ("unknown-root-key", "include: [a]\nbogus: 1\n", "unknown key(s) 'bogus'"),
    (
        "unknown-nested-scope-key",
        "include: [{path: a, include: [{path: b, bogus: 1}]}]\n",
        "include[0].include[0]: unknown key(s) 'bogus'",
    ),
    (
        "secret-patterns-in-nested-scope",
        "include: [{path: a, include: [b], secret_patterns: []}]\n",
        "unknown key(s) 'secret_patterns'",
    ),
    ("absolute-include-path", "include: [/abs]\n", "path '/abs' must be relative"),
    ("parent-traversal", "include: ['../up']\n", "must not contain '..'"),
    ("empty-include-path", "include: ['']\n", "path must be a non-empty string"),
    (
        "unknown-include-item-key",
        "include: [{path: a, allow_orphan: true}]\n",
        "unknown key(s) 'allow_orphan'",
    ),
    (
        "include-mapping-without-path",
        "include: [{optional: true}]\n",
        "mapping include items require a 'path' key",
    ),
    (
        "include-item-not-a-string",
        "include: [1]\n",
        "include items must be strings or mappings",
    ),
    (
        "exclude-item-not-a-string",
        "include: [a]\nexclude: [1]\n",
        "exclude items must be strings or mappings",
    ),
    (
        "glob-with-nested-scope",
        "include: [{path: 'a*', include: [b]}]\n",
        "glob include items cannot carry a nested include/exclude scope",
    ),
    (
        "non-boolean-optional",
        "include: [a]\nexclude: [{pattern: 'p', optional: 1}]\n",
        "'optional' must be a boolean",
    ),
    (
        "invalid-exclude-regex",
        "include: [a]\nexclude: ['[unclosed']\n",
        "invalid regex '[unclosed'",
    ),
    (
        "secret-patterns-not-a-list",
        "include: [a]\nsecret_patterns: 'x'\n",
        "'secret_patterns' must be a list",
    ),
    (
        "invalid-secret-regex",
        "include: [a]\nsecret_patterns: ['[bad']\n",
        "secret_patterns[0]: invalid regex '[bad'",
    ),
    (
        "include-matched-by-own-exclude",
        "include: [a]\nexclude: ['^a$']\n",
        "include item 'a' is excluded by pattern '^a$'",
    ),
    (
        "include-under-excluded-ancestor",
        "include: ['a/b/c']\nexclude: ['^a$']\n",
        "include item 'a/b/c' is nested beneath excluded path 'a'",
    ),
    (
        "glob-under-excluded-ancestor",
        "include: ['a/*']\nexclude: ['^a$']\n",
        "include item 'a/*' is nested beneath excluded path 'a'",
    ),
    (
        "exclude-not-a-list",
        "include: [a]\nexclude: 'x'\n",
        "'exclude' must be a list",
    ),
    (
        "include-path-not-a-string",
        "include: [{path: 1}]\n",
        "'path' must be a non-empty string",
    ),
    (
        "unknown-exclude-item-key",
        "include: [a]\nexclude: [{pattern: 'p', bogus: 1}]\n",
        "unknown key(s) 'bogus'",
    ),
    (
        "exclude-mapping-without-pattern",
        "include: [a]\nexclude: [{optional: true}]\n",
        "mapping exclude items require a 'pattern' key",
    ),
    (
        "exclude-pattern-not-a-string",
        "include: [a]\nexclude: [{pattern: 1}]\n",
        "'pattern' must be a non-empty string",
    ),
    (
        "secret-pattern-not-a-string",
        "include: [a]\nsecret_patterns: [1]\n",
        "secret_patterns[0]: must be a non-empty regex string",
    ),
]


@pytest.mark.parametrize(
    ("manifest_text", "message"),
    [(text, message) for _, text, message in INVALID_MANIFESTS],
    ids=[name for name, _, _ in INVALID_MANIFESTS],
)
def test_invalid_manifest_raises_config_error(tmp_path, manifest_text, message):
    config = tmp_path / "dotfiles.yaml"
    config.write_text(manifest_text)

    with pytest.raises(ConfigError, match=re.escape(message)):
        Manifest.load(config)


def test_missing_manifest_reports_the_read_failure(tmp_path):
    with pytest.raises(ConfigError, match="cannot read manifest"):
        Manifest.load(tmp_path / "absent.yaml")


def test_shipped_manifest_parses():
    manifest = Manifest.load(DEFAULT_CONFIG_PATH)
    paths = [item.path for item in manifest.root.include]

    assert paths
    assert len(paths) == len(set(paths))
    assert manifest.secret_patterns


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
