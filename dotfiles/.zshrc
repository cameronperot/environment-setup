# Antigen, pinned to a release for reproducibility; bump the tag deliberately
ANTIGEN_URL="https://raw.githubusercontent.com/zsh-users/antigen/v2.2.3/bin/antigen.zsh"
if [ ! -s "${HOME}/.antigen/antigen.zsh" ]; then
    mkdir -p "${HOME}/.antigen"
    wget -O "${HOME}/.antigen/antigen.zsh" "$ANTIGEN_URL" || {
        rm -f "${HOME}/.antigen/antigen.zsh"
        echo "zshrc: could not download antigen from $ANTIGEN_URL" >&2
        return 1
    }
fi
source "${HOME}/.antigen/antigen.zsh"

# Antigen config
antigen use oh-my-zsh

# Plugins
antigen bundle git
antigen bundle vi-mode
antigen bundle dnf
antigen bundle ssh-agent
antigen bundle colored-man-pages
# Pinned to tags for reproducibility; antigen only accepts tags
antigen bundle zsh-users/zsh-completions@0.36.0
antigen bundle Aloxaf/fzf-tab@v1.3.0
antigen bundle zsh-users/zsh-autosuggestions@v0.7.1
antigen bundle zsh-users/zsh-syntax-highlighting@0.8.0
antigen bundle zsh-users/zsh-history-substring-search@v1.1.0 # must be sourced last

# Start the agent and load keys on first ssh, not at shell startup
zstyle :omz:plugins:ssh-agent lazy yes

# Antigen apply
antigen apply

# history-substring-search
bindkey -M vicmd "k" history-substring-search-up
bindkey -M vicmd "j" history-substring-search-down

# Prompt theme
ZSH_THEME_GIT_PROMPT_PREFIX="("
ZSH_THEME_GIT_PROMPT_SUFFIX=")"
ZSH_THEME_GIT_PROMPT_DIRTY="*"
ZSH_THEME_GIT_PROMPT_CLEAN=""
PROMPT='%B%{$fg[green]%}%n@%m %{$fg[blue]%}%2~%b%{$fg[cyan]%}$(git_prompt_info)%{$reset_color%} ⟩ '
MODE_INDICATOR="%F{yellow}+%f"
RPROMPT=''

# http://zsh.sourceforge.net/Doc/Release/Options.html#Description-of-Options
setopt EXTENDED_GLOB
setopt EXTENDED_HISTORY
setopt HIST_IGNORE_SPACE
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_NO_STORE
setopt HIST_REDUCE_BLANKS
setopt HIST_VERIFY
setopt HIST_SAVE_NO_DUPS
unsetopt SHARE_HISTORY
HISTORY_IGNORE="(*password*|*secret*|*PASSWORD*|*SECRET*)"

# Aliases

# Key bindings (insert mode; main keymap is viins via vi-mode)
bindkey -s "^r" " ranger^M" # ctrl-r -> ranger
bindkey -s "^n" " nvim^M"   # ctrl-n -> nvim
bindkey -s "^h" " hstr^M"   # ctrl-h -> hstr
alias hh=hstr               # hh -> hstr
KEYTIMEOUT=1                # for esc in zsh vim mode

# Exports
[[ -t 0 ]] && export GPG_TTY="$(tty)"

# Source files
for file in .bash_aliases .local_aliases .local_exports
do
    if [ -f "${HOME}/${file}" ]; then
        source "${HOME}/${file}"
    fi
done

# Kitty complete (cached; regenerated when the kitty binary changes)
if [ -x "$(command -v kitty)" ]; then
    _kitty_cache="${XDG_CACHE_HOME:-$HOME/.cache}/kitty-zsh-completions.zsh"
    if [[ ! -s "$_kitty_cache" || "$(command -v kitty)" -nt "$_kitty_cache" ]]; then
        _kitty_tmp="$(mktemp "${_kitty_cache}.XXXXXX")"
        if kitty + complete setup zsh >| "$_kitty_tmp" && [[ -s "$_kitty_tmp" ]]; then
            mv "$_kitty_tmp" "$_kitty_cache"
        else
            rm -f "$_kitty_tmp"
        fi
    fi
    [[ -s "$_kitty_cache" ]] && source "$_kitty_cache"
    unset _kitty_cache _kitty_tmp
fi

# Micromamba
if [[ -f "${HOME}/.mamba_init.sh" ]]; then
    source "${HOME}/.mamba_init.sh"
fi

# zoxide
if [ -x "$(command -v zoxide)" ]; then
    eval "$(zoxide init zsh --cmd z)" # defines z and zi (zi needs fzf)
fi
