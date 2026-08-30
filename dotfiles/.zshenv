# Path
if [ -d "$HOME/.local/bin" ]; then
    case ":$PATH:" in
        *:"$HOME/.local/bin":*) ;;
        *) export PATH="$HOME/.local/bin${PATH:+:${PATH}}" ;;
    esac
fi
if [ -d "$HOME/bin" ]; then
    case ":$PATH:" in
        *:"$HOME/bin":*) ;;
        *) export PATH="$HOME/bin${PATH:+:${PATH}}" ;;
    esac
fi

# History
export HISTFILE="$HOME/.zsh_history"
export HISTSIZE=1000000
export SAVEHIST=$HISTSIZE

# hstr
export HSTR_CONFIG=hicolor       # get more colors
export HSTR_CONFIG=prompt-bottom # place prompt at bottom

# Rust
if [ -d "$HOME/.cargo/bin" ]; then
    case ":$PATH:" in
        *:"$HOME/.cargo/bin":*) ;;
        *) export PATH="${PATH:+$PATH:}$HOME/.cargo/bin" ;;
    esac
fi
if [ -f "$HOME/.cargo/env" ]; then
    . "$HOME/.cargo/env"
fi

# Ruby
if [ -d "$HOME/gems/bin" ]; then
    case ":$PATH:" in
        *:"$HOME/gems/bin":*) ;;
        *) export PATH="${PATH:+$PATH:}$HOME/gems/bin" ;;
    esac
fi
export BUNDLE_FORCE_RUBY_PLATFORM=true
export GEM_HOME="$HOME/gems"

# Editor
export VISUAL="nvim"
export EDITOR="nvim"
export SYSTEMD_EDITOR="nvim"
export JULIA_EDITOR="nvim"

# Language
export LC_ALL=en_US.UTF8
export LANG=en_US.UTF-8
export LANGUAGE=en_US.UTF-8

# Misc.
export VI_MODE_SET_CURSOR=true
export KEYTIMEOUT=1 # for esc in zsh vim mode
export QT_QPA_PLATFORMTHEME=qt5ct
export NO_AT_BRIDGE=1 # https://unix.stackexchange.com/questions/230238/x-applications-warn-couldnt-connect-to-accessibility-bus-on-stderr
export GPG_TTY=$(tty)
export LIBVIRT_DEFAULT_URI="qemu:///system"
export SHELL=/usr/bin/zsh
export DOCKER_HOST="unix:///run/user/$(id -u)/podman/podman.sock"
unset RANGER_LOAD_DEFAULT_RC

# Juliaup
if [ -d "$HOME/.juliaup/bin" ]; then
    case ":$PATH:" in
        *:"$HOME/.juliaup/bin":*) ;;
        *) export PATH="$HOME/.juliaup/bin${PATH:+:${PATH}}" ;;
    esac
fi
