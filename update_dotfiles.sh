#!/usr/bin/env bash
set -eu -o pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd -P )"

# copy over dotfiles
rsync -a "${HOME}/.zshrc" "${DIR}/dotfiles/.zshrc"
rsync -a "${HOME}/.zshenv" "${DIR}/dotfiles/.zshenv"
rsync -a "${HOME}/.tmux.conf" "${DIR}/dotfiles/.tmux.conf"
rsync -a "${HOME}/.XCompose" "${DIR}/dotfiles/.XCompose"
rsync -a "${HOME}/.config/htop/" "${DIR}/dotfiles/.config/htop/"
rsync -a "${HOME}/.config/nvim/init.vim" "${DIR}/dotfiles/.config/nvim/init.vim"
rsync -a "${HOME}/.config/i3/config" "${DIR}/dotfiles/.config/i3/config"
rsync -a "${HOME}/.config/i3status/config" "${DIR}/dotfiles/.config/i3status/config"
rsync -a "${HOME}/.config/ranger/" "${DIR}/dotfiles/.config/ranger/"
rsync -a "${HOME}/.config/Code/User/settings.json" "${DIR}/dotfiles/.config/Code/User/settings.json"
rsync -a "${HOME}/.config/Code/User/keybindings.json" "${DIR}/dotfiles/.config/Code/User/keybindings.json"
rsync -a "${HOME}/.config/Code/User/extensions.list" "${DIR}/dotfiles/.config/Code/User/extensions.list"

# commit and push
cd "${DIR}"
git add dotfiles
git commit -m "Updated dotfiles"
git push
