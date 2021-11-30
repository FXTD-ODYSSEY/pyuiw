# -*- coding: utf-8 -*-
"""

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
import isort


__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2021-11-28 20:13:19"


def test_basic_parse(runner, get_ui):
    ui_file, py_file = get_ui("custom")
    args = [ui_file]
    runner(args)
    assert py_file.is_file()


def test_no_isort(runner, get_ui):
    ui_file, py_file = get_ui("custom")
    args = ["-ni", ui_file]
    runner(args)
    assert py_file.is_file()
    assert isort.file(str(py_file))


def test_no_black(runner, get_ui):
    ui_file, py_file = get_ui("custom")
    args = ["-nb", ui_file]
    runner(args)
    assert py_file.is_file()
    with open(py_file, encoding="utf-8") as f:
        src = f.read()

    subprocess.call([sys.executable, "-m", "black", py_file])

    with open(py_file, encoding="utf-8") as f:
        content = f.read()

    assert src != content


def test_output(runner, get_ui):
    ui_file, py_file = get_ui("custom", "custom.py")
    args = ["-o=<${ui_dir}/${ui_name}.py>", ui_file]
    runner(args)
    assert py_file.is_file()


def test_ts(runner, get_ui):
    ui_file, py_file = get_ui("custom", "custom.py")
    ts_file = Path(str(py_file.parent / py_file.stem) + ".ts")
    args = ["-o=<${ui_dir}/${ui_name}.py>", "-ts=<${ui_dir}/${ui_name}.ts>", ui_file]
    runner(args)
    assert py_file.is_file()
    assert ts_file.is_file()
