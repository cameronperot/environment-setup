---
name: changelog
description: Maintains CHANGELOG.md files in Keep a Changelog format — creates changelogs, drafts entries, cuts releases. Use only when explicitly asked to update a changelog, write release notes, or cut a release. Do not invoke proactively after user-facing changes.
disable-model-invocation: true
---

# Changelog

Maintain `CHANGELOG.md` following [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Arguments

Trailing input after `/skill:changelog` selects the workflow:

- `init` → Initialize.
- `release`, optionally with a version (e.g. `release 2.0.0`) → Cut a release.
- Any other text → a description of changes for Add entries.

Conversational requests map the same way.
With no input, default to Add entries.

## Format rules

- Changelogs are for humans: describe the user-facing impact of a change, not its implementation. Never paste commit messages or `git log` output as entries.
- Keep one `## [Unreleased]` section at the top; released versions follow in reverse chronological order.
- Version headings are `## [X.Y.Z] - YYYY-MM-DD`. Dates are ISO 8601; get today's date with `date +%F`, never from memory.
- Group entries under these headings in this order, omitting empty ones: `### Added`, `### Changed`, `### Deprecated`, `### Removed`, `### Fixed`, `### Security`.
- One change per bullet, verb-first sentence style ("Added retry logic to the order client"). Reference issue or PR numbers where they help readers.
- Prefix breaking changes with `**Breaking:**` — they force a major version bump.
- Version headings are markdown link references. Maintain the link block at the bottom of the file: `[Unreleased]` compares the latest tag to `HEAD`, each version compares to its predecessor, and the oldest version links to its release tag. Derive URLs from `git remote get-url origin`; if there is no remote, omit the link block entirely rather than writing placeholder links.
- Keep yanked releases listed and mark them: `## [0.4.0] - 2026-01-10 [YANKED]`.
- Record every deprecation under `### Deprecated` — it is the warning users need before a removal.
- Never rewrite released sections except to fix factual errors or add `[YANKED]`.

## Add entries

1. Locate `CHANGELOG.md` at the repo root. If it is missing, run Initialize first.
2. Determine what changed. Prefer the user's description or the current session's edits. Otherwise inspect history: find the last release tag with `git describe --tags --abbrev=0`, then read `git log <tag>..HEAD` and the corresponding diffs; if no tags exist, use the commits since the last change to `CHANGELOG.md`.
3. Rewrite each change as a user-facing entry under the correct category in `[Unreleased]`. Skip internal-only noise (CI tweaks, refactors with no observable effect) unless the user asks to include it.

## Cut a release

1. Confirm `[Unreleased]` is non-empty and covers everything since the last tag; run Add entries for anything missing.
2. Use the version the user named. Otherwise derive it from the `[Unreleased]` content: any breaking change → major, anything under Added, Changed, Deprecated, or Removed → minor, only Fixed or Security → patch. Before 1.0.0, breaking changes may ship in a minor bump.
3. Rename `[Unreleased]` to `[X.Y.Z] - <today>` and insert a fresh `## [Unreleased]` heading above it.
4. Update the link block: add the new version's compare link and repoint `[Unreleased]` to compare from the new tag.
5. Do not tag, commit, or publish unless asked.

## Initialize

Create `CHANGELOG.md` at the repo root with the preamble and empty `[Unreleased]` section shown in the example.
Offer to backfill released versions from existing git tags, but only do so if the user accepts; date each backfilled version from its tag (`git log -1 --format=%as <tag>`).

## Example

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-08-19

### Added

- Added a `--dry-run` flag to `sync` that reports pending changes without applying them ([#42](https://github.com/acme/sync/pull/42)).

### Changed

- Changed the default sync interval from 60s to 30s.

### Fixed

- Fixed a crash when the config file contains unknown keys.

## [1.0.0] - 2026-07-02

### Added

- Initial release.

[Unreleased]: https://github.com/acme/sync/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/acme/sync/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/acme/sync/releases/tag/v1.0.0
```

Rewriting a commit into an entry:

| Commit message | Changelog entry |
|---|---|
| `fix(ws): reconnect on 1006, bump ping interval, refactor handler` | Fixed dropped websocket connections not reconnecting after abnormal closes. |

## Existing non-standard changelogs

If the repo already maintains its changelog in a different consistent format, follow that format and tell the user, instead of converting it unasked.
