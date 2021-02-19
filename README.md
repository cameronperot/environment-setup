# Environment Setup
This repo is automates the setup of a programming environment consisting of zsh, tmux, neovim, and ranger.

## Usage
Clone the repo and run the install script:
```bash
git clone https://github.com/cameronperot/environment-setup.git
cd environment-setup
./install.sh
```

Optional: to install the setup using a miniconda Python installation located at `/opt/miniconda3/bin/python3`, pass `local` as the first argument to the install script (note that this will **not** install the following packages via `pip` `python-language-server[all] black flake8 neovim ranger-fm`):
```bash
./install.sh local
```

### Customization
If you would like to adapt this repo to your config, you can modify the `update_dotfiles.sh` script to copy your doftiles to the dotfiles directory, and the `install.sh` script to install your desired software and copy over your dotfiles.
