# initialize
source $HOME/antigen.zsh
source $HOME/.bash_aliases


# antigen config
antigen use oh-my-zsh

# plugins
antigen bundle git
antigen bundle vi-mode
antigen bundle docker
antigen bundle docker-compose
antigen bundle dnf
antigen bundle rsync
#antigen bundle ssh-agent
antigen bundle pip
antigen bundle common-aliases
antigen bundle command-not-found
antigen bundle unixorn/git-extra-commands
antigen bundle zsh-users/zsh-syntax-highlighting
antigen bundle zsh-users/zsh-completions
antigen bundle zsh-users/zsh-autosuggestions
antigen bundle zsh-users/zsh-history-substring-search

# antigen apply
antigen apply

# prompt theme
ZSH_THEME_GIT_PROMPT_PREFIX="("
ZSH_THEME_GIT_PROMPT_SUFFIX=")"
ZSH_THEME_GIT_PROMPT_DIRTY="*"
ZSH_THEME_GIT_PROMPT_CLEAN=""
PROMPT='%B%{$fg[green]%}%n@%m %{$fg[blue]%}%2~%b%{$fg[cyan]%}$(git_prompt_info)%{$reset_color%} ⟩ '
RPROMPT=''

# history
export HISTFILE="$HOME/.zsh_history"
export HISTSIZE=1000000
export SAVEHIST=$HISTSIZE
export HISTCONTROL=ignorespace:ignoredups:erasedups # leading space hides commands from history

# kitty complete
#source <(kitty + complete setup zsh)

# julia specific env vars
export JULIA_LOAD_PATH="$JULIA_LOAD_PATH:$HOME/rsync/programming/GraphEvolve.jl/src"
export JULIA_LOAD_PATH="$JULIA_LOAD_PATH:$HOME/rsync/programming/MagSim.jl/src"
export JULIA_LOAD_PATH="$JULIA_LOAD_PATH:$HOME/rsync/programming/FuNN.jl/src"
export JULIA_EDITOR="nvim"

# install Ruby Gems to ~/gems
export BUNDLE_FORCE_RUBY_PLATFORM=true
export GEM_HOME="$HOME/gems"
export PATH="$HOME/gems/bin:$PATH"

# misc.
export QT_QPA_PLATFORMTHEME=qt5ct
export PATH="$HOME/bin:$PATH"
export PATH="$HOME/.local/bin:$PATH"
export NO_AT_BRIDGE=1 # https://unix.stackexchange.com/questions/230238/x-applications-warn-couldnt-connect-to-accessibility-bus-on-stderr
export VISUAL=nvim
export EDITOR=nvim
export RANGER_LOAD_DEFAULT_RC=FALSE
unalias rm
bindkey -s "^r" " ranger^M" # bind ctrl-r to ranger
bindkey -s "^n" " nvim^M"   # bind ctrl-n to nvim

# transfer.sh
transfer(){ if [ $# -eq 0 ];then echo "No arguments specified.\nUsage:\n  transfer <file|directory>\n  ... | transfer <file_name>">&2;return 1;fi;if tty -s;then file="$1";file_name=$(basename "$file");if [ ! -e "$file" ];then echo "$file: No such file or directory">&2;return 1;fi;if [ -d "$file" ];then file_name="$file_name.zip" ,;(cd "$file"&&zip -r -q - .)|curl --progress-bar --upload-file "-" "https://transfer.sh/$file_name"|tee /dev/null,;else cat "$file"|curl --progress-bar --upload-file "-" "https://transfer.sh/$file_name"|tee /dev/null;fi;else file_name=$1;curl --progress-bar --upload-file "-" "https://transfer.sh/$file_name"|tee /dev/null;fi;}

# HSTR configuration - add this to ~/.bashrc
bindkey -s "^h" " hstr^M"         # bind ctrl-h to hstr
alias hh=hstr                    # hh to be alias for hstr
export HSTR_CONFIG=hicolor       # get more colors
export HSTR_CONFIG=prompt-bottom # place prompt at bottom
setopt histignorespace           # skip cmds w/ leading space from history
unsetopt share_history           # disable sharing of history between sessions
