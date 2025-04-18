#!/usr/bin/env bash
set -eu -o pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd -P)"

# copy over dotfiles
rsync -a --mkpath "${HOME}/.XCompose" "${DIR}/dotfiles/.XCompose"
rsync -a --mkpath "${HOME}/.conda_init.sh" "${DIR}/dotfiles/.conda_init.sh"
rsync -a --mkpath "${HOME}/.config/Code/User/extensions.list" "${DIR}/dotfiles/.config/Code/User/extensions.list"
rsync -a --mkpath "${HOME}/.config/Code/User/keybindings.json" "${DIR}/dotfiles/.config/Code/User/keybindings.json"
rsync -a --mkpath "${HOME}/.config/Code/User/settings.json" "${DIR}/dotfiles/.config/Code/User/settings.json"
rsync -a --mkpath "${HOME}/.config/black.conf" "${DIR}/dotfiles/.config/"
rsync -a --mkpath "${HOME}/.config/btop/btop.conf" "${DIR}/dotfiles/.config/btop/btop.conf"
rsync -a --mkpath "${HOME}/.config/fuzzel/fuzzel.ini" "${DIR}/dotfiles/.config/fuzzel/fuzzel.ini"
rsync -a --mkpath "${HOME}/.config/gammastep/config.ini" "${DIR}/dotfiles/.config/gammastep/config.ini"
rsync -a --mkpath "${HOME}/.config/htop/" "${DIR}/dotfiles/.config/htop/"
rsync -a --mkpath "${HOME}/.config/i3/config" "${DIR}/dotfiles/.config/i3/config"
rsync -a --mkpath "${HOME}/.config/i3status-rust/config.toml" "${DIR}/dotfiles/.config/i3status-rust/config.toml"
rsync -a --mkpath "${HOME}/.config/kitty/kitty.conf" "${DIR}/dotfiles/.config/kitty/kitty.conf"
rsync -a --mkpath "${HOME}/.config/nvim/init.lua" "${DIR}/dotfiles/.config/nvim/init.lua"
rsync -a --mkpath "${HOME}/.config/nvim/lua/" "${DIR}/dotfiles/.config/nvim/lua/"
rsync -a --mkpath "${HOME}/.config/ranger/" "${DIR}/dotfiles/.config/ranger/"
rsync -a --mkpath "${HOME}/.config/sway/config" "${DIR}/dotfiles/.config/sway/config"
rsync -a --mkpath "${HOME}/.tmux.conf" "${DIR}/dotfiles/.tmux.conf"
rsync -a --mkpath "${HOME}/.zshenv" "${DIR}/dotfiles/.zshenv"
rsync -a --mkpath "${HOME}/.zshrc" "${DIR}/dotfiles/.zshrc"

# commit and push
cd "${DIR}"
git add dotfiles
git commit -m "Updated dotfiles"
git push
