# -*- coding: utf-8 -*-
"""
Command Line Watcher for auto compile Qt ui to python file.

Usage Example:
"""

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
import argparse
import copy
import fnmatch
from functools import partial
from io import open
import os
from pathlib import Path
import signal
from string import Template
import subprocess
import sys

# Import third-party modules
import Qt
from Qt import QtCore
from Qt import QtWidgets
import isort
import toml

# Import local modules
from pyuiw.uic import __version__ as PySideUicVersion
from pyuiw.uic.driver import Driver


__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2020-12-04 10:50:02"


FILE = Path(__file__)
DIR = FILE.parent
signal.signal(signal.SIGINT, signal.SIG_DFL)


if sys.hexversion >= 0x03000000:
    # Import local modules
    from pyuiw.uic.port_v3.invoke import invoke
else:
    # Import local modules
    from pyuiw.uic.port_v2.invoke import invoke

Version = "Qt User Interface Compiler version %s, running on %s %s." % (
    PySideUicVersion,
    Qt.__binding__,
    Qt.QtCore.qVersion(),
)


class CliBase(object):
    def __init__(self):
        self.default_exp = "<${py_dir}/${py_name}_ui.py>"
        self.parser = argparse.ArgumentParser(
            prog="pyuiw",
            formatter_class=argparse.RawTextHelpFormatter,
            description=Version + __doc__,
        )

    def is_exp(self, exp):
        return exp.startswith("<") and exp.endswith(">")

    def parse_exp(self, exp, ui_file):
        ui_file = Path(ui_file)
        is_exp = self.is_exp(exp)
        if is_exp:
            template = Template(exp[1:-1])
            exp = template.substitute(
                {"py_name": ui_file.stem, "py_dir": ui_file.parent}
            )
            exp = os.path.abspath(exp)
        return exp

    def parse_config(self):

        config = getattr(self.opts, "config", "./pyproject.toml")
        config = Path(config)
        if not config.is_file():
            return [], []

        watch_list = []
        exclude_list = []
        with open(config, "r") as f:
            config = toml.load(f)
        tool = config.get("tool", {})
        pyuiw = tool.get("pyuiw", {})

        watch_list = pyuiw.get("watch", [])
        exclude_list = pyuiw.get("exclude", [])

        os.environ["pyuiw_isUseQt"] = str(pyuiw.get("useQt", True)).lower()
        os.environ["pyuiw_QtModule"] = pyuiw.get("QtModule", "Qt")

        output = pyuiw.get("output", self.default_exp)
        if output != self.default_exp == self.opts.output:
            self.opts.output = output

        indent = pyuiw.get("indent", 4)
        if indent != 4 == self.opts.indent:
            self.opts.indent = indent

        execute = pyuiw.get("execute", True)
        if execute != True == self.opts.execute:
            self.opts.execute = execute

        debug = pyuiw.get("debug", False)
        if debug != False == self.opts.debug:
            self.opts.debug = debug

        preview = pyuiw.get("preview", False)
        if preview != False == self.opts.preview:
            self.opts.preview = preview

        from_imports = pyuiw.get("from_imports", False)
        if from_imports != False == self.opts.from_imports:
            self.opts.from_imports = from_imports

        black = pyuiw.get("black", True)
        if black != True == self.opts.black:
            self.opts.black = black

        isort = pyuiw.get("isort", True)
        if isort != True == self.opts.isort:
            self.opts.isort = isort

        return watch_list, exclude_list

    def parse(self):
        self.opts, args = self.parser.parse_known_args()

        watch_list, exclude_list = self.parse_config()
        watch_list = getattr(self.opts, "watch", watch_list)
        exclude_list = getattr(self.opts, "exclude", exclude_list)

        # NOTES: add environment variable
        if hasattr(self.opts, "useQt"):
            os.environ["pyuiw_isUseQt"] = self.opts.useQt
        if hasattr(self.opts, "QtModule"):
            os.environ["pyuiw_QtModule"] = self.opts.QtModule

        ui_file = args[0] if args else ""
        if ui_file or not watch_list or not self.is_exp(self.opts.output):
            return self.parse_single_ui(ui_file)

        self.watch(watch_list, exclude_list)

    def watch(self, watch_list, exclude_list):
        app = QtWidgets.QApplication(sys.argv)
        watcher = QtCore.QFileSystemWatcher()

        paths = []
        print(watch_list)
        for path in watch_list:
            path = Path(path.strip())
            if path.is_file():
                paths.append(str(path))
            elif path.is_dir():
                for root, dirs, files in os.walk(path):
                    root = Path(root)
                    for f in files:
                        if f.endswith(".ui"):
                            paths.append(str(root / f))

        # NOTES filter path
        for exclude in exclude_list:
            for f in fnmatch.filter(paths, exclude):
                paths.remove(f)

        if not paths:
            sys.stderr.write("Error: no find any ui file in watch path\n")
            sys.exit(0)

        print("watch ui files:")
        print("\n".join(paths))
        print(f"\n{'=' * 40}\n")

        for ui_file in paths:
            self.parse_single_ui(ui_file)
            watcher.addPath(str(ui_file))

        watcher.fileChanged.connect(self.on_file_change)
        app.exec_()

    def on_file_change(self, ui_file):
        self.parse_single_ui(ui_file)

    def parse_single_ui(self, ui_file):
        ui_file = Path(ui_file)
        if not ui_file.is_file():
            self.parser.print_usage()
            sys.stderr.write("Error: one input ui-file must be specified\n")
            return

        opts = copy.deepcopy(self.opts)
        opts.output = self.parse_exp(self.opts.output, ui_file)
        ui_file = str(ui_file.absolute())

        # FIXME: some ui file output empty in watch mode
        invoke(Driver(opts, ui_file))

        if opts.black:
            subprocess.call([sys.executable, "-m", "black", opts.output])
        if opts.isort:
            isort.file(opts.output)

        print("[pyuiw] output: ", opts.output)


class PyUIWatcherCli(CliBase):
    def __init__(self):
        super(PyUIWatcherCli, self).__init__()
        self.parser.add_argument(
            "-p",
            "--preview",
            dest="preview",
            action="store_false",
            default=False,
            help="show a preview of the UI instead of generating code",
        )
        self.parser.add_argument(
            "-o",
            "--output",
            dest="output",
            action="store",
            type=str,
            default=self.default_exp,
            metavar="FILE",
            help="\n".join(
                [
                    "write generated code to FILE instead of stdout",
                    f"<EXP> to define a output expression (default: {self.default_exp})",
                    r"${py_dir} - input python directory path",
                    r"${py_name} - input python file name",
                ]
            ),
        )
        self.parser.add_argument(
            "-x",
            "--execute",
            dest="execute",
            action="store_true",
            default=True,
            help="generate extra code to test and display the class",
        )
        self.parser.add_argument(
            "-d",
            "--debug",
            dest="debug",
            action="store_false",
            default=False,
            help="show debug output",
        )
        self.parser.add_argument(
            "-i",
            "--indent",
            dest="indent",
            action="store",
            type=int,
            default=4,
            metavar="N",
            help="set indent width to N spaces, tab if N is 0 (default: 4)",
        )

        g = self.parser.add_argument_group(title="Code generation options")
        g.add_argument(
            "--from-imports",
            dest="from_imports",
            action="store_true",
            default=False,
            help="generate imports relative to '.'",
        )
        g.add_argument(
            "--useQt",
            dest="useQt",
            action="store_true",
            default=argparse.SUPPRESS,
            help="using Qt.py module for Qt compat",
        )
        g.add_argument(
            "--QtModule",
            dest="QtModule",
            action="store",
            type=str,
            default=argparse.SUPPRESS,
            metavar="module",
            help="customize import Qt module name | only work in --useQt false",
        )
        g.add_argument(
            "-nb",
            "--no-black",
            dest="black",
            action="store_false",
            default=True,
            help="using black format code",
        )
        g.add_argument(
            "-ni",
            "--no-isort",
            dest="isort",
            action="store_false",
            default=True,
            help="using isort format code",
        )
        self.parser.add_argument_group(g)

        g = self.parser.add_argument_group(title="Watcher options")
        g.add_argument(
            "-w",
            "--watch",
            dest="watch",
            nargs="+",
            type=str,
            default=argparse.SUPPRESS,
            help="watch files or directories",
        )
        g.add_argument(
            "-e",
            "--exclude",
            dest="exclude",
            nargs="+",
            type=str,
            default=argparse.SUPPRESS,
            help="exclude files glob expression",
        )
        g.add_argument(
            "-c",
            "--config",
            dest="config",
            default=argparse.SUPPRESS,
            metavar="FILE",
            help="read specific config file",
        )

        self.parser.add_argument_group(g)

        self.parse()
        sys.exit(0)


if __name__ == "__main__":
    PyUIWatcherCli()
