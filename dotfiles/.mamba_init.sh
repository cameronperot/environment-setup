# Micromamba initialization
export MAMBA_EXE="/home/user/micromamba/bin/micromamba"
export MAMBA_ROOT_PREFIX="/home/user/micromamba"
__mamba_setup="$("$MAMBA_EXE" shell hook --shell zsh --root-prefix "$MAMBA_ROOT_PREFIX" 2>/dev/null)"
if [ $? -eq 0 ]; then
    eval "$__mamba_setup"
else
    alias micromamba="$MAMBA_EXE"
fi
unset __mamba_setup
micromamba activate dev
