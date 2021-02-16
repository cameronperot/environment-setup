#!/usr/bin/env bash
set -eu -o pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd -P)"

# copy over dotfiles
rsync -avz --progress -h $HOME/.zshrc $DIR/dotfiles/.zshrc
rsync -avz --progress -h $HOME/.tmux.conf $DIR/dotfiles/.tmux.conf
rsync -avz --progress -h $HOME/.config/nvim/init.vim $DIR/dotfiles/.config/nvim/init.vim
rsync -avz --progress -h $HOME/.config/ranger/ $DIR/dotfiles/.config/ranger/
