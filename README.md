# Development Environment

Configuration and setup scripts for a Linux development environment built around zsh, tmux, Neovim and ranger, with optional dotfiles for sway/i3, kitty and related desktop tooling. Also includes a [dev container](dev-container/README.md) for sandboxed LLM-assisted coding and instructions for a [KVM/QEMU dev VM](dev-vm/README.md).

## Layout
| Path | Purpose |
| :--- | :--- |
| `install.py` | Rsyncs `dotfiles/` into `$HOME`, installs Neovim, and adjusts the deployed copies to the host |
| `dotfiles/` | Tracked dotfiles: zsh, tmux, Neovim, ranger, git, coding-agent config, and `.config/` for sway, i3, kitty, VS Code and more |
| `dotfiles/bin/` | User scripts deployed to `~/bin`: `c`, `agent-sandbox`, `agent-shadow`, `git-bareify` |
| `dotfiles.yaml` | Manifest for `sync_dotfiles.py`: what to sync, exclude and watch |
| `sync_dotfiles.py` | Copies dotfiles from `$HOME` back into `dotfiles/`, the reverse of `install.py` |
| `environment.yml` | Micromamba environment `dev` (Python and core tooling) |
| `python/environments/` | Further micromamba environments: `base`, `data`, `dev`, `finance`, `jupyter`, `ml` |
| `julia/julia-setup.jl` | Installs the default Julia package set |
| `dev-container/` | Dev container image, compose file and entrypoint; the root `.containerignore` filters its build context |
| `dev-vm/` | KVM + QEMU + libvirt VM instructions |
| `tests/` | Pytest suite for `install.py`, `sync_dotfiles.py` and `dotfiles/bin/c` |
| `pyproject.toml` | Pytest and coverage configuration (the repo is not a Python package) |
| `Makefile` | Shortcuts for the commands below (`make help`) |

## Install
Requires `rsync`, plus `wget` when Neovim is installed.
```bash
git clone https://github.com/cameronperot/environment-setup.git
cd environment-setup
./install.py   # or: make install
```
Options:
- `--neovim-version <version>`: Neovim release to install (default `stable`; `none` skips it)
- `--extract-appimage`: extract the appimage instead of running it directly (systems without FUSE)
- `--dry-run`: preview the dotfile changes without modifying anything

`make install` takes `NEOVIM_VERSION=vX.Y.Z` and `EXTRACT_APPIMAGE=1` for the same options.

## Toolchains
| Command | Effect |
| :--- | :--- |
| `make mamba-install` | Install micromamba |
| `make mamba-init` | Initialize micromamba for the current shell |
| `make mamba-env` | Create the `dev` environment from `environment.yml` |
| `micromamba create -f python/environments/<name>.yml` | Create one of the additional environments |
| `make rust-install` | Install Rust via rustup |
| `make juliaup-install` | Install Julia via Juliaup |
| `julia julia/julia-setup.jl` | Install the default Julia packages |
| `make container-build` | Build the dev container image (see its [README](dev-container/README.md)) |

## Updating Dotfiles
`sync_dotfiles.py` pulls dotfiles from `$HOME` into `dotfiles/`. It reports changes `git status`-style but never commits or pushes; review and commit yourself, or pass `--stage` to `git add` the result.
```bash
make update-dotfiles                          # real sync
make update-dotfiles DOTFILES_ARGS=--dry-run  # preview without touching anything
make update-dotfiles DOTFILES_ARGS=--check    # terse; exit 2 when changes are pending
uv run sync_dotfiles.py --status              # report without syncing
uv run sync_dotfiles.py --discover            # audit untracked dotfiles in $HOME
uv run sync_dotfiles.py --prune               # also delete orphaned repo files and copies of entries missing in $HOME
```
Exit codes: `0` success (a real sync exits 0 whether or not it applied changes), `1` error, `2` changes pending (`--dry-run` and `--check` only), so `--check` slots into cron or CI.

### Manifest (`dotfiles.yaml`)
Every scope, from `$HOME` down to individual directories, has `include:` and `exclude:` lists, and a directory include entry may carry a nested scope of the same shape with its lists relative to that directory:
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
- `include` items are literal paths or fnmatch globs (`*`, `?`, `**`), as plain strings or mappings (`path:` plus `optional:` and, for directories, a nested scope).
- A nested scope may carry `include:`, `exclude:` or both; an `include:` curates the directory, and files outside the selection are orphans unless an `allow_orphan` exclude tolerates them.
- `exclude` items are regexes with search semantics (anchors control scope), matched against paths relative to the declaring scope; a match prunes the whole subtree and silences the untracked watch there.
- Repository files beneath an exclude are orphans (warned about, deleted by `--prune`) unless the exclude has `allow_orphan: true`, which keeps them in the repo while the `$HOME` side stays untracked.
- The untracked watch warns about top-level `$HOME` dot-entries and contents of curated directories that no entry covers (e.g. a new `~/.newtool`); fix it by adding an include or exclude to the enclosing scope. `--discover` lists the same candidates.
- Exclude patterns that match nothing produce an unused-pattern warning unless marked `optional: true`.
- Outgoing files are scanned for secret signatures (private key blocks, AWS keys, credential assignments) plus `secret_patterns`; flagged files are skipped with a warning, or abort the run under `--strict-secrets`.
- Symlinks, and glob matches that pass through a symlinked directory, are skipped with a warning unless `--follow-symlinks` is given.
