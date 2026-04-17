from __future__ import (absolute_import, division, print_function)

import os
import shutil
import subprocess

from ranger.api.commands import Command


class fzf_select(Command):
    """:fzf_select

    Pick a file or directory with fzf and jump to it.
    Uses fd/fdfind if available, otherwise find.
    """

    def execute(self):
        start = self.fm.thisdir.path

        if shutil.which("fdfind"):
            finder = "fdfind --hidden --follow --exclude .git . "
        elif shutil.which("fd"):
            finder = "fd --hidden --follow --exclude .git . "
        else:
            finder = "find -L "
        cmd = finder + self._q(start) + " | fzf +m"

        fzf = self.fm.execute_command(
            cmd, universal_newlines=True, stdout=subprocess.PIPE
        )
        out, _ = fzf.communicate()
        if fzf.returncode != 0:
            return
        picked = out.strip()
        if not picked:
            return
        picked = os.path.abspath(picked)
        if os.path.isdir(picked):
            self.fm.cd(picked)
        else:
            self.fm.select_file(picked)

    @staticmethod
    def _q(s):
        return "'" + s.replace("'", "'\\''") + "'"
