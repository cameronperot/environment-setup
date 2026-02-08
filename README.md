# Environment Setup
This repo automates the setup of a programming environment consisting of zsh, tmux, neovim, and ranger.

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

## Devcontainers
Devcontainers CLI can be installed with:
```bash
npm install -g @devcontainers/cli
```

## Programming Languages
### Python
Micromamba can be installed by running:
```bash
curl -Ls https://raw.githubusercontent.com/cameronperot/shell-scripts/refs/heads/master/scripts/install_micromamba.sh | bash
```
and initialized with:
```bash
~/micromamba/bin/micromamba shell init --root-prefix ~/micromamba
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
Julia can be downloaded and installed from the [Julia downloads page](https://julialang.org/downloads/).

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
