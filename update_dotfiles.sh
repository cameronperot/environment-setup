#!/usr/bin/env bash
set -eu -o pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd -P)"

# copy over dotfiles
rsync -avz --progress -h $HOME/.zshrc $DIR/dotfiles/.zshrc
rsync -avz --progress -h $HOME/.tmux.conf $DIR/dotfiles/.tmux.conf
rsync -avz --progress -h $HOME/.config/nvim/init.vim $DIR/dotfiles/.config/nvim/init.vim

# edit init.vim to mitigate possible issues on remote
sed -i "s/Plug 'iamcco\/markdown-preview.nvim'/\"Plug 'iamcco\/markdown-preview.nvim'/g" $DIR/dotfiles/.config/nvim/init.vim
sed -i "s/\/opt\/miniconda3\/bin\/python/\/usr\/bin\/python3/g" $DIR/dotfiles/.config/nvim/init.vim

# edit .zshrc to mitigate possible issues on remote
sed -i "s/source <(kitty + complete setup zsh)/#source <(kitty + complete setup zsh)/g" $DIR/dotfiles/.zshrc
sed -i "s/antigen bundle ssh-agent/#antigen bundle ssh-agent/g" $DIR/dotfiles/.zshrc
sed -i "s/source \$HOME\/.backblaze.sh//g" $DIR/dotfiles/.zshrc
