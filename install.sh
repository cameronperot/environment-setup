#!/usr/bin/env bash
set -eu -o pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd -P )"

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

# extras for remote installation
HOST=${1:-remote}
if [ "$HOST" == "remote" ]; then
    # edit init.vim to mitigate possible issues on remote
    sed -i "s/Plug 'iamcco\/markdown-preview.nvim'/\"Plug 'iamcco\/markdown-preview.nvim'/g" $DIR/dotfiles/.config/nvim/init.vim
    sed -i "s/\/opt\/miniconda3\/bin\/python/\/usr\/bin\/python3/g" $DIR/dotfiles/.config/nvim/init.vim

    # edit .zshrc to mitigate possible issues on remote
    sed -i "s/source <(kitty + complete setup zsh)/#source <(kitty + complete setup zsh)/g" $DIR/dotfiles/.zshrc
    sed -i "s/antigen bundle ssh-agent/#antigen bundle ssh-agent/g" $DIR/dotfiles/.zshrc

    # install python development packages
    pip3 install --user 'python-language-server[all]' black flake8 neovim

    # install ranger
    pip3 install --user ranger-fm
fi

# copy over dotfiles
rsync -av --progress --update $DIR/dotfiles/ $HOME/
