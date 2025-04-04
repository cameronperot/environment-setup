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
Ensure the required packages are installed by running the following in Neovim:
```
PackerSync
```
```
MasonInstall lua-language-server rust-analyzer codelldb pyright
```

To install pyright or rust-analyzer manually:
```bash
rustup component add rust-analyzer
```
```bash
npm install -g pyright
```

## Programming Languages
### Python
Miniconda can be installed with the `miniconda.sh` script.
After install, it is recommended to install the following packages:
```bash
conda install black flake8 pylint mypy pydantic nodejs yarn
pip install pynvim ranger-fm
```

Miniconda can be initialized with zsh by running:
```bash
~/miniconda3/bin/conda init zsh
```

### Rust
Rust can be installed using [rustup](https://rustup.rs/) with:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Treesitter might require the following package to be installed:
```
cargo install tree-sitter-cli
```

### Julia
Julia can be downloaded and installed from the [Julia downloads page](https://julialang.org/downloads/).

## Misc.
Zoxide is a nice alternative to using `cd`:
```bash
conda install -c conda-forge zoxide
```
or
```bash
cargo install zoxide --locked
```

## Customization
If you would like to adapt this repo to your config, you can modify the `update_dotfiles.sh` script to copy your doftiles to the dotfiles directory, and the `install.py` script to install your desired software and copy over your dotfiles.
