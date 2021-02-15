#!/usr/bin/env bash
set -eu -o pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd -P)"

# create ~/bin
if [ ! -d $HOME/bin ]; then
  mkdir -p $HOME/bin;
fi

# install nvim
wget -O $HOME/bin/nvim.appimage https://github.com/neovim/neovim/releases/download/nightly/nvim.appimage
chmod u+x $HOME/bin/nvim.appimage
cd $HOME/bin
./nvim.appimage --appimage-extract
ln -s $HOME/bin/squashfs-root/usr/bin/nvim $HOME/bin/nvim

# install tmux-resurrect
git clone https://github.com/tmux-plugins/tmux-resurrect $HOME/tmux-resurrect

# install antigen
curl -L git.io/antigen > $HOME/antigen.zsh

# copy over dotfiles
rsync -av --progress --update $DIR/dotfiles/ $HOME/

# install python language server
pip3 install --user 'python-language-server[all]' black flake8 neovim
