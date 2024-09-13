# Path
export PATH="$PATH:$HOME/gems/bin"
export PATH="$PATH:$HOME/.cargo/bin"
export PATH="$HOME/bin:$PATH"
export PATH="$HOME/.local/bin:$PATH"

# History
export HISTFILE="$HOME/.zsh_history"
export HISTSIZE=1000000
export SAVEHIST=$HISTSIZE

# hstr
export HSTR_CONFIG=hicolor       # get more colors
export HSTR_CONFIG=prompt-bottom # place prompt at bottom

# Ruby
export BUNDLE_FORCE_RUBY_PLATFORM=true
export GEM_HOME="$HOME/gems"

# Editor
export VISUAL=nvim
export EDITOR=nvim
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
export RANGER_LOAD_DEFAULT_RC=FALSE
export GPG_TTY=$(tty)
export LIBVIRT_DEFAULT_URI="qemu:///system"
export SHELL=/usr/bin/zsh
. "$HOME/.cargo/env"
