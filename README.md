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

Most repository commands are also available as Makefile targets:
```bash
make help
```

## Programming Languages
### Python
```bash
# install micromamba
curl -Ls https://raw.githubusercontent.com/cameronperot/shell-scripts/refs/heads/master/scripts/install_micromamba.sh | bash

# initialize for the current shell
~/.micromamba/bin/micromamba shell init --root-prefix ~/.micromamba

# create the root environment
micromamba create -f environment.yml
```

Additional environments live in `python/environments/` and are created the same way, e.g. `micromamba create -f python/environments/ml.yml`.

### Rust
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Julia
```bash
# install via Juliaup
curl -fsSL https://install.julialang.org | sh

# install the default package set
julia julia/julia-setup.jl
```

## Customization
To adapt this repo to your own setup, edit `update_dotfiles.sh` to copy your dotfiles into `dotfiles/`, and `install.py` to install your desired software and copy over your dotfiles.
