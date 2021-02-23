#!/usr/bin/env bash
set -eu -o pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd -P)"

# copy over dotfiles
rsync -avz --progress -h $HOME/.zshrc $DIR/dotfiles/.zshrc
rsync -avz --progress -h $HOME/.tmux.conf $DIR/dotfiles/.tmux.conf
rsync -avz --progress -h $HOME/.config/htop/ $DIR/dotfiles/.config/htop/
rsync -avz --progress -h $HOME/.config/nvim/init.vim $DIR/dotfiles/.config/nvim/init.vim
rsync -avz --progress -h $HOME/.config/i3/config $DIR/dotfiles/.config/i3/config
rsync -avz --progress -h $HOME/.config/i3status/config $DIR/dotfiles/.config/i3status/config
rsync -avz --progress -h $HOME/.config/ranger/ $DIR/dotfiles/.config/ranger/

cd $DIR
git add .
git commit -m "Updated dotfiles"
git push
