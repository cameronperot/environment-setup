# Development Environment
This repository contains configs and instructions for a development environment using zsh, tmux, neovim, ranger, containers, VMs, and virtual environments.

- [Dev Container](dev-container/README.md)
- [Dev VM](dev-vm/README.md)

## Usage
Clone the repo and run the install script:
```bash
git clone https://github.com/cameronperot/environment-setup.git
cd environment-setup
./install.py
```
For more information on the CLI args, run
```bash
./install.py --help
```

## Neovim
Some packages that might be required:
```bash
cargo install tree-sitter-cli stylua
```

## Programming Languages
### Python
Micromamba can be installed by running:
```bash
curl -Ls https://raw.githubusercontent.com/cameronperot/shell-scripts/refs/heads/master/scripts/install_micromamba.sh | bash
```
and initialized with:
```bash
~/.micromamba/bin/micromamba shell init --root-prefix ~/.micromamba
```
The environment can be installed by running:
```bash
micromamba create -f environment.yml
```

### Rust
Rust can be installed using [rustup](https://rustup.rs/) with:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Julia
Julia can be installed using [Juliaup](https://docs.julialang.org/en/v1/manual/installation/) with:
```bash
curl -fsSL https://install.julialang.org | sh
```
The environment can be installed by running:
```bash
julia julia/julia-setup.jl
```

## Misc.
Zoxide is a nice alternative to using `cd`:
```bash
cargo install zoxide --locked
```
or
```bash
micromamba install -c conda-forge zoxide
```

## Customization
If you would like to adapt this repo to your config, you can modify the `update_dotfiles.sh` script to copy your doftiles to the dotfiles directory, and the `install.py` script to install your desired software and copy over your dotfiles.
