# -*- coding: utf-8 -*-
""" """

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
from pathlib import Path
import subprocess
from textwrap import dedent
import time

# Import third-party modules
import pytest


__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2021-11-28 20:13:19"


def test_watch_files(runner, get_ui):
    custom, custom_py = get_ui("custom")
    blank, blank_py = get_ui("blank")
    basic, basic_py = get_ui("basic")
    blank_button, blank_button_py = get_ui("blank_button")

    args = ["-w", custom, blank, basic]
    process = runner(args, subprocess.Popen)
    time.sleep(3)
    assert custom_py.is_file()
    assert blank_py.is_file()
    assert basic_py.is_file()

    with open(blank_py, encoding="utf8") as f:
        before_py = f.read()

    with open(blank_button, encoding="utf8") as f:
        button_content = f.read()

    with open(blank, encoding="utf8") as f:
        content = f.read()

    with open(blank, "w", encoding="utf8") as f:
        f.write(button_content)

    time.sleep(2)

    with open(blank_py, encoding="utf8") as f:
        after_py = f.read()

    assert before_py != after_py
    process.terminate()

    with open(blank, "w", encoding="utf8") as f:
        f.write(content)


def test_watch_dir_and_exclude(runner, get_ui, UI_DIR):
    custom, custom_py = get_ui("custom")
    blank, blank_py = get_ui("blank")
    basic, basic_py = get_ui("basic")
    blank_button, blank_button_py = get_ui("blank_button")

    args = ["-w", str(UI_DIR), "-e", "*custom*"]
    process = runner(args, subprocess.Popen)
    time.sleep(3)
    assert not custom_py.is_file()
    assert blank_py.is_file()
    assert basic_py.is_file()

    with open(blank_py, encoding="utf8") as f:
        before_py = f.read()

    with open(blank_button, encoding="utf8") as f:
        button_content = f.read()

    with open(blank, encoding="utf8") as f:
        content = f.read()

    with open(blank, "w", encoding="utf8") as f:
        f.write(button_content)

    time.sleep(2)

    with open(blank_py, encoding="utf8") as f:
        after_py = f.read()

    assert before_py != after_py
    process.terminate()

    with open(blank, "w", encoding="utf8") as f:
        f.write(content)
