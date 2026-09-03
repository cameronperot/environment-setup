# Development Environment

Configuration and setup scripts for a Linux development environment built around zsh, tmux, Neovim, and ranger, with optional dotfiles for sway/i3, kitty, and related tooling. Also includes a dev container for sandboxed/LLM-assisted coding and instructions for a KVM/QEMU dev VM.

## Repository Layout
- `install.py` — rsyncs `dotfiles/` and installs neovim
- `dotfiles/` — tracked dotfiles (zsh, tmux, Neovim, ranger, sway, kitty, VS Code, etc.)
- `dotfiles/bin/` — user scripts rsynced to `~/bin`
- `dotfiles.yaml` — manifest driving `sync_dotfiles.py` (which files to sync, ignore, and watch)
- `sync_dotfiles.py` — copies dotfiles from your home directory back into `dotfiles/`
- `environment.yml` — root micromamba environment (Python + core tooling)
- `python/environments/` — additional micromamba environments (data, ml, finance, jupyter, dev)
- `julia/julia-setup.jl` — installs the default Julia package set
- `dev-container/` — [dev container](dev-container/README.md) for sandboxed coding
- `dev-vm/` — [dev VM](dev-vm/README.md) (KVM + QEMU + libvirt) instructions
- `Makefile` — shortcuts for all of the above

## Installation
```bash
git clone https://github.com/cameronperot/environment-setup.git
cd environment-setup
./install.py
```

CLI options:
```bash
./install.py --help
```

- `--neovim-version <version>` — Neovim release to install (default: `stable`; use `none` to skip)
- `--extract-appimage` — extract the appimage instead of running it directly (needed on systems without FUSE)
- `--dry-run` — preview the dotfile changes without modifying anything

Most repository commands are also available as Makefile targets:
```bash
make help
```

## Updating Dotfiles

`sync_dotfiles.py` pulls dotfiles from your home directory into `dotfiles/` (the reverse of `install.py`).
It reports changes but never commits or pushes; review the output and commit yourself, or pass `--stage` to `git add` the changes:

```bash
make update-dotfiles                          # real sync
make update-dotfiles DOTFILES_ARGS=--dry-run  # preview without touching anything
make update-dotfiles DOTFILES_ARGS=--check    # terse; exit 2 when changes are pending
uv run sync_dotfiles.py --status              # report without syncing
uv run sync_dotfiles.py --discover            # audit untracked dotfiles in $HOME
uv run sync_dotfiles.py --prune               # also delete orphaned repo files and copies of entries missing in $HOME
```

Exit codes: `0` success (a real sync exits 0 whether or not it applied changes), `1` error, `2` changes pending (`--dry-run`/`--check` only), so `--check` slots into cron or CI.

### Manifest (`dotfiles.yaml`)

The manifest is a tree of scopes built from a single recursive grammar: every scope, from `$HOME` down to individual directories, has `include:` and `exclude:` lists, and any directory include entry may carry a nested scope of the same shape, with its lists relative to that directory:

```yaml
include:                          # root scope: $HOME
  - .zshrc                        # plain string: file or directory
  - path: .config                 # directory carrying a nested scope
    include:
      - htop                      # whole subdirectory
      - path: Code/User           # nesting to any depth
        include: [settings.json, keybindings.json]
      - path: io.datasette.llm
        exclude: ['logs\.db$', 'keys\.json$']   # regex, relative to this entry
        optional: true            # may be missing in $HOME: no warning, never pruned
  - '.config/*/*.conf'            # glob include (`**` for recursive)
exclude:                          # root scope: patterns match $HOME-relative paths
  - '^\.cache$'                   # anchored: that top-level entry only
  - '\.bak$'                      # unanchored: any depth, under any include entry
  - pattern: '^\.config/pulse$'
    optional: true                # allowed to match nothing (no unused-pattern warning)
    allow_orphan: true            # repo copies beneath it are kept: no orphan warnings, never pruned
secret_patterns:                  # extra regexes for the secret guard
  - 'API_KEY\s*=\s*["''](?!\$)[^"'']{8,}["'']'
```

Semantics:
- `include` items are literal paths or fnmatch globs (`*`, `?`, `**`), as plain strings or mappings (`path:` plus `optional:` and, for directories, a nested scope).
- A nested scope may carry `include:`, `exclude:`, or both; with `include:` the directory's contents are curated, and files outside the selection surface as orphans (unless an `allow_orphan` exclude tolerates them, see below).
- `exclude` items are regexes with search semantics (anchors control scope) matched against paths relative to the scope where they are declared; a match prunes the whole subtree. Exclude patterns also silence the untracked watch within their scope. Repository files beneath an exclude are orphans (warned about and deleted by `--prune`) unless the exclude is marked `allow_orphan: true`, which tolerates them in the repo while the `$HOME` side stays untracked either way.
- The untracked watch warns about top-level `$HOME` dot-entries and the contents of curated directories that no entry covers (e.g. a new `~/.newtool`); resolve warnings by adding an include or an exclude to the enclosing scope. `--discover` reports the same candidates.
- Exclude patterns that match nothing during a run produce an unused-pattern warning unless marked `optional: true`.
- Outgoing (added or changed) files are scanned for secret signatures (private key blocks, AWS keys, credential assignments) plus `secret_patterns`; flagged files are skipped with a warning, or abort the run under `--strict-secrets`.
- Symlinks are skipped with a warning; `--follow-symlinks` dereferences them.
- Glob matches that pass through a symlinked directory mid-path (e.g. `link/x.conf` under `'.config/*/x.conf'`) are skipped the same way unless `--follow-symlinks` is given.
- Changes are reported `git status`-style after syncing; nothing is ever committed or pushed.
