#!/usr/bin/env bash
set -e

# >>> mamba initialize >>>
# !! Contents within this block are managed by 'micromamba shell init' !!
export MAMBA_EXE="${HOME}/micromamba/bin/micromamba"
export MAMBA_ROOT_PREFIX="${HOME}/micromamba"
__mamba_setup="$("$MAMBA_EXE" shell hook --shell zsh --root-prefix "$MAMBA_ROOT_PREFIX" 2>/dev/null)"
if [ $? -eq 0 ]; then
    eval "$__mamba_setup"
else
    alias micromamba="$MAMBA_EXE" # Fallback on help from micromamba activate
fi
unset __mamba_setup
# <<< mamba initialize <<<
