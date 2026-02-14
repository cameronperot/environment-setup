# Micromamba initialization
export MAMBA_ROOT_PREFIX="${MAMBA_ROOT_PREFIX:-${HOME}/.micromamba}"
export MAMBA_EXE="${MAMBA_ROOT_PREFIX}/bin/micromamba"

__mamba_setup="$("${MAMBA_EXE}" shell hook --shell zsh --root-prefix "${MAMBA_ROOT_PREFIX}" 2>/dev/null)"
if [ $? -eq 0 ]; then
    eval "$__mamba_setup"
else
    alias micromamba="${MAMBA_EXE}"
fi
unset __mamba_setup

if [ -x "${MAMBA_EXE}" ]; then
    if [ -d "${MAMBA_ROOT_PREFIX}/envs/dev" ]; then
        micromamba activate dev
    else
        micromamba activate base 2>/dev/null
    fi
fi
