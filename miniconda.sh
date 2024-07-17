#!/usr/bin/env bash
set -eu -o pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd -P)"

# Setting up the miniconda directory - default to ~/miniconda
INSTALL_DIR="${1:-${HOME}/miniconda3}"
CONDA_URL=https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
rm -rf "${INSTALL_DIR}"
mkdir "${INSTALL_DIR}"

# Download and run the installer
cd "${INSTALL_DIR}"
wget -O miniconda.sh "${CONDA_URL}"
bash miniconda.sh -b -f -p "${INSTALL_DIR}"
rm -f miniconda.sh

# Update and install packages
export PATH="${INSTALL_DIR}/bin:${PATH}"
conda update -y conda
