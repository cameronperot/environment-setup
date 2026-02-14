# General
alias clearnvimswap="rm ~/.local/state/nvim/swap/*.swp"
alias fd="fdfind"
alias mm="micromamba"
alias n="nvim"
alias nn="nvim --clean"
alias sn="sudoedit"
alias sshk="kitty +kitten ssh"
alias ta="tmux a"
alias updatenvim="wget -O /tmp/nvim.appimage https://github.com/neovim/neovim/releases/download/stable/nvim.appimage && mv /tmp/nvim.appimage ~/bin/nvim && chmod u+x ~/bin/nvim"

# LSD
alias l="lsd -lFh"      # long, classify, human-readable
alias la="lsd -lAFh"    # long, almost-all, classify, human-readable
alias lr="lsd -tRFh"    # tree, recursive, classify, human-readable
alias lt="lsd -ltFh"    # long, tree, classify, human-readable
alias ll="lsd -l"       # long
alias ldot="lsd -ld .*" # long, directory, dotfiles
alias lS="lsd -1FSh"    # one-per-line, classify, size-sort, human-readable
alias lart="lsd -1Fart" # one-per-line, classify, almost-all, reverse, timesort
alias lrt="lsd -1Frt"   # one-per-line, classify, reverse, timesort
alias lsr="lsd -lARFh"  # long, almost-all, recursive, classify, human-readable
alias lsn="lsd -1"      # one-per-line

# Podman
alias pm="podman"
alias pma="podman attach"
alias pmc="podman container"
alias pme="podman exec"
alias pmi="podman image"
alias pmp="podman pull"
alias pmr="podman run"
alias pmv="podman volume"
alias pmcom="podman-compose"

# systemctl user
alias svc="systemctl --user"
alias svc-logs="journalctl --user -u"
alias svc-reload="systemctl --user daemon-reload"
alias svc-restart="systemctl --user restart"
alias svc-restart-all="find ~/.config/containers/systemd/ -name '*.container' -exec basename {} .container \; | xargs -r systemctl --user restart"
alias svc-start="systemctl --user start"
alias svc-status="systemctl --user status"
alias svc-stop="systemctl --user stop"
alias svc-stop-all="find ~/.config/containers/systemd/ -name '*.container' -exec basename {} .container \; | xargs -r systemctl --user stop"
alias svc-list="systemctl --user list-units --type=service --state=running | grep -v -i 'healthcheck'"

# dev_container
alias c='podman run \
  -it \
  --rm \
  --userns=keep-id \
  --security-opt label=disable \
  -e GEMINI_API_KEY="${GEMINI_API_KEY}" \
  -e OPENROUTER_API_KEY="${OPENROUTER_API_KEY}" \
  -v dev-antigen:/home/dev/.antigen \
  -v dev-amp-config:/home/dev/.config/amp \
  -v dev-amp-data:/home/dev/.local/share/amp \
  -v dev-claude-config:/home/dev/.claude \
  -v dev-opencode-config:/home/dev/.config/opencode \
  -v dev-opencode-data:/home/dev/.local/share/opencode \
  -v ${PWD}:/work \
  dev:latest'
