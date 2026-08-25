# Development Environment

Configuration and setup scripts for a Linux development environment built around zsh, tmux, Neovim, and ranger, with optional dotfiles for sway/i3, kitty, and related tooling. Also includes a dev container for sandboxed/LLM-assisted coding and instructions for a KVM/QEMU dev VM.

## Repository Layout
- `install.py` — rsyncs `dotfiles/` and installs neovim
- `dotfiles/` — tracked dotfiles (zsh, tmux, Neovim, ranger, sway, kitty, VS Code, etc.)
- `update_dotfiles.sh` — copies dotfiles from your home directory back into `dotfiles/` and pushes
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
