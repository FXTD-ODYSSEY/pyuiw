# -*- coding: utf-8 -*-
""" """

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
import subprocess
import sys

# Import third-party modules
import toml


__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2021-11-30 22:33:11"


with open("pyproject.toml") as f:
    data = toml.load(f)

version = data["tool"]["poetry"]["version"]

subprocess.call(["poetry", "build"])
subprocess.call(["python", "-m", "pip", "uninstall", "-y", "pyuiw"])
subprocess.call(
    ["python", "-m", "pip", "install", f"dist/pyuiw-{version}-py3-none-any.whl"]
)
subprocess.call(["pyuiw", "tests/ui/custom.ui"])
