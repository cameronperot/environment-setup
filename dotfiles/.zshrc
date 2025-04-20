# Download antigen if it doesn't exist
if [ ! -f "${HOME}/antigen.zsh" ]; then
    wget -O "${HOME}/antigen.zsh" https://raw.githubusercontent.com/zsh-users/antigen/master/bin/antigen.zsh
fi

# Initialize
source "${HOME}/antigen.zsh"
for file in .profile .bash_aliases .secret_exports
do
    if [ -f "${HOME}/$file" ]; then
        source "${HOME}/$file"
    fi
done

# Antigen config
antigen use oh-my-zsh

# Plugins
antigen bundle git
antigen bundle vi-mode
antigen bundle docker
antigen bundle dnf
antigen bundle rsync
antigen bundle ssh-agent
antigen bundle pip
antigen bundle common-aliases
antigen bundle command-not-found
antigen bundle zsh-users/zsh-syntax-highlighting
antigen bundle zsh-users/zsh-completions
antigen bundle zsh-users/zsh-autosuggestions
antigen bundle zsh-users/zsh-history-substring-search

# Antigen apply
antigen apply

# Prompt theme
ZSH_THEME_GIT_PROMPT_PREFIX="("
ZSH_THEME_GIT_PROMPT_SUFFIX=")"
ZSH_THEME_GIT_PROMPT_DIRTY="*"
ZSH_THEME_GIT_PROMPT_CLEAN=""
PROMPT='%B%{$fg[green]%}%n@%m %{$fg[blue]%}%2~%b%{$fg[cyan]%}$(git_prompt_info)%{$reset_color%} ⟩ '
MODE_INDICATOR="%F{yellow}+%f"
RPROMPT=''

# http://zsh.sourceforge.net/Doc/Release/Options.html#Description-of-Options
setopt EXTENDED_HISTORY
setopt HIST_IGNORE_SPACE
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_NO_STORE
setopt HIST_REDUCE_BLANKS
setopt HIST_VERIFY
setopt HIST_SAVE_NO_DUPS
unsetopt SHARE_HISTORY

# Kitty complete
if [ -x "$(command -v kitty)" ]; then
    source <(kitty + complete setup zsh)
fi

# HSTR configuration - add this to ~/.bashrc
bindkey -s "^h" " hstr^M"        # bind ctrl-h to hstr
alias hh=hstr                    # hh to be alias for hstr

# zoxide
if [ -x "$(command -v zoxide)" ]; then
    function z () {
        __zoxide_z "$@"
    }
    eval "$(zoxide init zsh --no-cmd)"
fi

# Aliases
unalias rm
bindkey -s "^r" " ranger^M" # bind ctrl-r to ranger
bindkey -s "^n" " nvim^M"   # bind ctrl-n to nvim
if [ -f "${HOME}/.bash_aliases" ]; then
    source "${HOME}/.bash_aliases"
fi

# Micromamba
if [ -f "${HOME}/.mamba_init.sh" ]; then
    source "${HOME}/.mamba_init.sh"
    micromamba activate dev
fi
