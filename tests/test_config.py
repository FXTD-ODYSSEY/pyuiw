# -*- coding: utf-8 -*-
"""

"""

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
from collections import defaultdict
from textwrap import dedent

# Import third-party modules
import toml


__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2021-11-29 09:33:53"


nestdict = lambda: defaultdict(nestdict)


def test_config(runner, get_ui, UI_DIR):
    config_path = UI_DIR / "config.toml"
    data = nestdict()
    pyuiw = data["tool"]["pyuiw"]
    pyuiw["useQt"] = False

    with open(config_path, "w", encoding="utf-8") as f:
        toml.dump(data, f)

    ui_file, py_file = get_ui("custom")
    args = ["-c", config_path, ui_file]
    runner(args)

    with open(py_file, encoding="utf-8") as f:
        content = f.read()

    assert "QtCompat" not in content
