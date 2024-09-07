#!/usr/bin/env python3
import argparse
import logging
import os
import subprocess
from pathlib import Path


class EnvironmentInstaller:
    """
    Class to orchestrate the environment installation.
    """

    def __init__(self, neovim_version="v0.10.1", extract_appimage=False):
        """
        Initialize ``EnvironmentInstaller``.

        :param neovim_version: Version of Neovim to install. Available versions can be
            found here: https://github.com/neovim/neovim/releases. Defaults to
            ``"v0.9.4"``.
        :type neovim_version: str, optional
        :param extract_appimage: Flag to extract the appimage (might be necessary if
            FUSE isn't available). Defaults to ``False``.
        :type extract_appimage: bool, optional
        """
        self._repo_dir = Path(__file__).parent
        self._home_dir = Path().home()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._neovim_version = neovim_version
        self._extract_appimage = extract_appimage

        # configure the logger
        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s %(asctime)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # change to the repo directory
        os.chdir(self._repo_dir)

    def _run_command(self, command):
        """
        Run the provided command, logging the command itself as well as the STDOUT.

        :param command: Command to run.
        :type command: list[str]
        """
        # log the command
        self._logger.info(f"⟩ {' '.join(str(x) for x in command)}")

        # run the command and log the STDOUT
        result = subprocess.run(
            command, check=True, capture_output=True, encoding="utf-8"
        )
        if result.stdout:
            self._logger.info(result.stdout)

        return result

    def install_neovim(self):
        """
        Install Neovim to the user's home bin directory (~/bin/nvim).
        """
        self._logger.info("Installing Neovim")

        # ensure the install path exists
        nvim_path = self._home_dir / "bin/nvim"
        if not nvim_path.parent.exists():
            nvim_path.parent.mkdir()
        os.chdir(nvim_path.parent)

        # appimage url and commands to download and mark it as executable
        url = f"https://github.com/neovim/neovim/releases/download/{self._neovim_version}/nvim.appimage"
        commands = [
            ["wget", "-O", nvim_path, url],
            ["chmod", "u+x", nvim_path],
        ]

        # if extracting, then we have to run additional commands
        if self._extract_appimage:
            commands += [
                [nvim_path, "--appimage-extract"],
                ["rm", nvim_path],
                [
                    "ln",
                    "-s",
                    nvim_path.parent / "squashfs-root/usr/bin/nvim",
                    nvim_path,
                ],
            ]
        else:
            commands += [["mv", nvim_path, nvim_path.parent / "nvim"]]

        # run the commands
        for command in commands:
            self._run_command(command)

        # change back to the repo directory
        os.chdir(self._repo_dir)

        self._logger.info("Successfully installed Neovim")

    def install_tmux_resurrect(self):
        """
        Install tmux-resurrect to the user's home directory (~/tmux-resurrect).
        """
        self._logger.info("Installing tmux-resurrect")

        # repo url and path to clone the repo to
        url = "https://github.com/tmux-plugins/tmux-resurrect"
        clone_path = self._home_dir / "tmux-resurrect"

        # run the command
        command = ["git", "clone", url, clone_path]
        self._run_command(command)

        self._logger.info("Successfully installed tmux-resurrect")

    def modify_zshrc(self):
        """
        Modify the .zshrc file to comment out any lines that might cause issues on
        remote hosts.
        """
        self._logger.info("Modifying .zshrc")

        # path to the .zshrc
        file_path = self._repo_dir / "dotfiles/.zshrc"

        # lines to comment out
        comment_lines = (
            "antigen bundle ssh-agent",
            "source <(kitty + complete setup zsh)",
        )

        # read the lines from the file
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # comment out the necessary lines
        lines = [
            line
            if not any(line.startswith(pattern) for pattern in comment_lines)
            else f"# {line}"
            for line in lines
        ]

        # write the lines back to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        self._logger.info("Successfully modified .zshrc")

    def copy_doftiles(self):
        """
        Copy over the dotfiles to the user's home directory.
        """
        self._logger.info("Copying dotfiles")

        # source and destination directories to copy dotfiles from and to
        source_dir = self._repo_dir / "dotfiles"
        dest_dir = self._home_dir

        # run the command
        command = ["rsync", "-av", str(source_dir) + "/", str(dest_dir) + "/"]
        self._run_command(command)

        self._logger.info("Successfully copied dotfiles")

    def run(self):
        """
        Run all install methods in sequence.
        """
        self.install_neovim()
        self.install_tmux_resurrect()
        self.modify_zshrc()
        self.copy_doftiles()


if __name__ == "__main__":
    # configure the argument parser
    parser = argparse.ArgumentParser(
        description="CLI for installing/configuring an Linux user environment.",
    )
    parser.add_argument(
        "--neovim-version",
        action="store",
        type=str,
        default="v0.10.1",
        metavar="<NVIM_VERSION>",
        help="Version of Neovim to install, e.g., v0.10.1 or nightly.",
    )
    parser.add_argument(
        "--extract-appimage",
        action="store_true",
        help="Extract the appimage (necessary on systems without FUSE).",
    )
    args = parser.parse_args()

    # initialize and run the installer
    installer = EnvironmentInstaller(
        neovim_version=args.neovim_version, extract_appimage=args.extract_appimage
    )
    installer.run()
