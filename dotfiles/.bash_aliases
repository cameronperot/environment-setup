# misc.
alias clearbashhist="cat /dev/null > ~/.bash_history && history -c && exit"
alias clearnvimswap="rm ~/.local/share/nvim/swap/*.swp"
alias sshk="kitty +kitten ssh"
alias vi="nvim"
alias vin="nvim --clean"
alias svi="sudoedit"
alias ta="tmux a -t"
alias updatenvim="wget -O /tmp/nvim.appimage https://github.com/neovim/neovim/releases/download/nightly/nvim.appimage && mv /tmp/nvim.appimage ~/bin/nvim && chmod u+x ~/bin/nvim"

# podman
alias pm="podman"
alias pma="podman attach"
alias pmc="podman container"
alias pme="podman exec"
alias pmi="podman image"
alias pmp="podman pull"
alias pmr="podman run"
alias pmv="podman volume"
alias pmcom="podman-compose"

# LSD
alias l="lsd -lFh"
alias la="lsd -lAFh"
alias lr="lsd -tRFh"
alias lt="lsd -ltFh"
alias ll="lsd -l"
alias ldot="lsd -ld .*"
alias lS="lsd -1FSsh"
alias lart="lsd -1Fcart"
alias lrt="lsd -1Fcrt"
alias lsr="lsd -lARFh"
alias lsn="lsd -1"

# conda
alias ca="source ~/.conda_init.sh"
alias cadev="source ~/.conda_init.sh && conda activate dev"
