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

### Customization
If you would like to adapt this repo to your config, you can modify the `update_dotfiles.sh` script to copy your doftiles to the dotfiles directory, and the `install.py` script to install your desired software and copy over your dotfiles.
