# Path
# Precedence: ~/bin > ~/.local/bin > ~/.cargo/bin > ~/.juliaup/bin > inherited PATH > ~/gems/bin
for _path_dir in "${HOME}/.juliaup/bin" "${HOME}/.cargo/bin" "${HOME}/.local/bin" "${HOME}/bin"; do
    if [[ -d "${_path_dir}" ]]; then
        case ":${PATH}:" in
        *":${_path_dir}:"*) ;;
        *) PATH="${_path_dir}:${PATH}" ;;
        esac
    fi
done
if [[ -d "${HOME}/gems/bin" ]]; then
    case ":${PATH}:" in
    *":${HOME}/gems/bin:"*) ;;
    *) PATH="${PATH}:${HOME}/gems/bin" ;; # after inherited PATH
    esac
fi
unset _path_dir
export PATH

# History
# HISTFILE stays at bash's default ~/.bash_history; the zsh and bash history
# formats are not interchangeable
export HISTSIZE=1000000
export HISTFILESIZE=${HISTSIZE}

# hstr
export HSTR_CONFIG="hicolor prompt-bottom" # more colors, place prompt at bottom

# Ruby
export BUNDLE_FORCE_RUBY_PLATFORM=true
export GEM_HOME="${HOME}/gems"

# Editor
export VISUAL="nvim"
export EDITOR="nvim"
export SYSTEMD_EDITOR="nvim"
export JULIA_EDITOR="nvim"

# Language
export LANG=en_US.UTF-8

# Misc.
export QT_QPA_PLATFORMTHEME="qt5ct:qt6ct" # Qt5 and Qt6 theming; needs qt5ct/qt6ct packages
export NO_AT_BRIDGE=1                     # https://unix.stackexchange.com/questions/230238/x-applications-warn-couldnt-connect-to-accessibility-bus-on-stderr
export LIBVIRT_DEFAULT_URI="qemu:///system"
DOCKER_HOST="unix:///run/user/$(id -u)/podman/podman.sock"
export DOCKER_HOST
unset RANGER_LOAD_DEFAULT_RC

# Everything below is interactive-only.
if [[ $- != *i* ]]; then
    return
fi

# Prompt theme
__bash_prompt_dir() {
    local n=2 rel
    local -a segs
    if [[ "${PWD}" == "${HOME}" ]]; then
        segs=("~")
    elif [[ "${PWD}" == "${HOME}"/* ]]; then
        rel="${PWD#"${HOME}"/}"
        IFS=/ read -r -a segs <<<"${rel}"
        segs=("~" "${segs[@]}")
    else
        IFS=/ read -r -a segs <<<"${PWD#/}"
    fi
    if ((${#segs[@]} <= n)); then
        if [[ "${segs[0]:-}" == "~" ]]; then
            if ((${#segs[@]} == 1)); then
                printf '~'
            else
                local IFS=/
                # shellcheck disable=SC2088 # literal ~, not a path to expand
                printf '~/%s' "${segs[*]:1}"
            fi
        else
            printf '%s' "${PWD}"
        fi
    else
        local IFS=/
        printf '%s' "${segs[*]: -${n}}"
    fi
}

__bash_git_prompt() {
    local branch
    branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" || return 0
    if [[ -z "${branch}" ]]; then
        return 0
    fi
    local dirty=""
    if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
        dirty="*"
    fi
    printf '(%s%s)' "${branch}" "${dirty}"
}
PS1='\[\e[1;32m\]\u@\h \[\e[1;34m\]$(__bash_prompt_dir)\[\e[0m\]\[\e[36m\]$(__bash_git_prompt)\[\e[0m\] ⟩ '

# https://www.gnu.org/software/bash/manual/bash.html#The-Shopt-Builtin
shopt -s extglob        # EXTENDED_GLOB
shopt -s histappend     # history is not shared, so append instead of clobbering
shopt -s histverify     # HIST_VERIFY
HISTTIMEFORMAT='%F %T ' # EXTENDED_HISTORY
HISTCONTROL=ignorespace:ignoredups:erasedups
HISTIGNORE='history:history *:fc *:*password*:*secret*:*PASSWORD*:*SECRET*'

# Aliases
alias hh=hstr # hh -> hstr

# Key bindings (vi mode, history search and the ctrl-r/n/h macros) are in .inputrc

# Exports
if [[ -t 0 ]]; then
    GPG_TTY="$(tty)"
    export GPG_TTY
fi

# Source files
for file in .bash_aliases .local_aliases .local_exports; do
    if [[ -f "${HOME}/${file}" ]]; then
        # shellcheck source=/dev/null
        source "${HOME}/${file}"
    fi
done
unset file

# Completions
if [[ -r /usr/share/bash-completion/bash_completion ]]; then
    source /usr/share/bash-completion/bash_completion
elif [[ -r /etc/bash_completion ]]; then
    source /etc/bash_completion
fi

# colored-man-pages
export LESS_TERMCAP_mb=$'\e[1;31m'    # begin blinking
export LESS_TERMCAP_md=$'\e[1;31m'    # begin bold
export LESS_TERMCAP_me=$'\e[0m'       # end mode
export LESS_TERMCAP_se=$'\e[0m'       # end standout
export LESS_TERMCAP_so=$'\e[1;44;33m' # begin standout (info box)
export LESS_TERMCAP_ue=$'\e[0m'       # end underline
export LESS_TERMCAP_us=$'\e[1;32m'    # begin underline

# Kitty complete (cached; regenerated when the kitty binary changes)
if [[ -x "$(command -v kitty)" ]]; then
    _kitty_cache="${XDG_CACHE_HOME:-${HOME}/.cache}/kitty-bash-completions.bash"
    if [[ ! -s "${_kitty_cache}" || "$(command -v kitty)" -nt "${_kitty_cache}" ]]; then
        _kitty_tmp="$(mktemp "${_kitty_cache}.XXXXXX")"
        if kitty + complete setup bash >|"${_kitty_tmp}" && [[ -s "${_kitty_tmp}" ]]; then
            mv "${_kitty_tmp}" "${_kitty_cache}"
        else
            rm -f "${_kitty_tmp}"
        fi
    fi
    # shellcheck source=/dev/null
    [[ -s "${_kitty_cache}" ]] && source "${_kitty_cache}"
    unset _kitty_cache _kitty_tmp
fi

# Micromamba
if [[ -f "${HOME}/.mamba_init.sh" ]]; then
    # shellcheck source=/dev/null
    source "${HOME}/.mamba_init.sh"
fi

# zoxide
if [[ -x "$(command -v zoxide)" ]]; then
    eval "$(zoxide init bash --cmd z)" # defines z and zi (zi needs fzf)
fi
