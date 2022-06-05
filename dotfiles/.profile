# History
export HISTFILE="$HOME/.zsh_history"
export HISTSIZE=1000000
export SAVEHIST=$HISTSIZE

# histr
export HSTR_CONFIG=hicolor       # get more colors
export HSTR_CONFIG=prompt-bottom # place prompt at bottom

# Julia specific env vars
export JULIA_EDITOR="nvim"

# Install Ruby Gems to ~/gems
export BUNDLE_FORCE_RUBY_PLATFORM=true
export GEM_HOME="$HOME/gems"
export PATH="$PATH:$HOME/gems/bin"

# Add rust to path
export PATH="$PATH:$HOME/.cargo/bin"

# Misc.
export VI_MODE_SET_CURSOR=true
export QT_QPA_PLATFORMTHEME=qt5ct
export PATH="$HOME/bin:$PATH"
export PATH="$HOME/.local/bin:$PATH"
export NO_AT_BRIDGE=1 # https://unix.stackexchange.com/questions/230238/x-applications-warn-couldnt-connect-to-accessibility-bus-on-stderr
export VISUAL=nvim
export EDITOR=nvim
export RANGER_LOAD_DEFAULT_RC=FALSE
export LC_ALL=en_US.UTF8
export LANG=en_US.UTF-8
export LANGUAGE=en_US.UTF-8
export KEYTIMEOUT=1 # for esc in zsh vim mode
