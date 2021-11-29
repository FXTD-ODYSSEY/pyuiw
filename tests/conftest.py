# -*- coding: utf-8 -*-
"""
pytest conf
"""

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
from pathlib import Path
import subprocess
import sys

# Import third-party modules
import pytest


__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2021-11-28 20:14:49"


FILE = Path(__file__)


@pytest.fixture
def runner():
    def runner(args=[], call=subprocess.check_output):
        commands = [
            sys.executable,
            "./pyuiw/__main__.py",
        ] + args

        msg = call(commands)
        return msg

    return runner


@pytest.fixture
def UI_DIR():
    return FILE.parent / "ui"


@pytest.fixture
def get_ui():
    def get_ui(ui="blank", py=None):
        ui_dir = FILE.parent / "ui"
        py = f"{ui}_ui.py" if py is None else py
        ui_file = str(ui_dir / f"{ui}.ui")
        py_file = ui_dir / py
        py_file.is_file() and py_file.unlink()
        return ui_file, py_file

    return get_ui
