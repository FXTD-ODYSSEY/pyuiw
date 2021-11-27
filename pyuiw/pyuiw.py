# -*- coding: utf-8 -*-
"""
Command Line Watcher for auto compile Qt ui to python file.

Usage Example:
pass
"""

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2020-12-04 10:50:02"

# Import built-in modules
import argparse
from io import open
import os
from pathlib import Path
import signal
import subprocess
import sys

# Import third-party modules
import Qt
from Qt import QtCore
from Qt import QtWidgets
from pyside2uic import __version__ as PySideUicVersion
from pyside2uic.driver import Driver
import toml


if sys.hexversion >= 0x03000000:
    # Import third-party modules
    from pyside2uic.port_v3.invoke import invoke
else:
    # Import third-party modules
    from pyside2uic.port_v2.invoke import invoke

Version = "Qt User Interface Compiler version %s, running on %s %s." % (
    PySideUicVersion,
    Qt.__binding__,
    Qt.QtCore.qVersion(),
)

signal.signal(signal.SIGINT, signal.SIG_DFL)
FILE = Path(__file__)
DIR = FILE.parent


class WatcherBase(object):
    def is_exp(self, exp):
        return exp.startswith("<") and exp.endswith(">")

    def parse_exp(self, exp, ui_file):
        ui_file = Path(ui_file)
        is_exp = self.is_exp(exp)
        if is_exp:
            exp = exp[1:-1] % {"py": ui_file.parent / ui_file.stem}
        return exp

    def watch(self, watch_list, exclude_list):

        app = QtWidgets.QApplication(sys.argv)
        watcher = QtCore.QFileSystemWatcher()

        paths = []
        for path in watch_list:
            path = Path(path)
            if path.is_file():
                paths.append(path)
                watcher.addPath(str(path))
            elif path.is_dir():
                for root, dirs, files in os.walk(path):
                    root = Path(root)
                    for f in files:
                        if f.endswith(".ui"):
                            path = str(root / f)
                            paths.append(path)
                            watcher.addPath(path)

        print("watch ui files:\n" + "\n".join(paths))
        watcher.fileChanged.connect(self.on_file_change)
        app.exec_()

    def on_file_change(self, ui_file):
        ui_py = self.parse_exp(self.opts.output, ui_file)
        # FIXME(timmyliang): command line exe
        subprocess.call([sys.executable, __file__, "-o", ui_py, ui_file])


class ParserBase(WatcherBase):
    def parse_config(self):
        watch_list = []
        exclude_list = []
        config = getattr(self.opts, "config", "./pyproject.toml")
        config = Path(config)
        if config.is_file():
            with open(config, "r") as f:
                config = toml.load(f)
            tool = config.get("tool", {})
            pyuiw = tool.get("pyuiw", {})
            watch_list = pyuiw.get("watch", [])
            exclude_list = pyuiw.get("exclude", [])

        return watch_list, exclude_list

    def parse_single_ui(self, args):
        ui_file = args[0] if args else ""
        ui_file = Path(ui_file)
        if not ui_file.is_file():
            self.parser.print_usage()
            sys.stderr.write("Error: one input ui-file must be specified\n")
            sys.exit(1)

        self.opts.output = self.parse_exp(self.opts.output, ui_file)
        invoke(Driver(self.opts, str(ui_file)))
        print("output: ", self.opts.output)
        sys.exit(1)

    def parse(self):
        self.opts, args = self.parser.parse_known_args()

        # NOTES: add environment variable
        if hasattr(self.opts, "useQt"):
            os.environ["pyuiw_isUseQt"] = self.opts.useQt
        if hasattr(self.opts, "QtModule"):
            os.environ["pyuiw_QtModule"] = self.opts.QtModule

        watch_list, exclude_list = self.parse_config()
        watch_list = getattr(self.opts, "watch", watch_list)
        exclude_list = getattr(self.opts, "exclude", exclude_list)

        if not watch_list or not self.is_exp(self.opts.output):
            return self.parse_single_ui(args)

        self.watch(watch_list, exclude_list)


class PyUIWatcherCli(ParserBase):
    def __init__(self):

        self.parser = argparse.ArgumentParser(
            prog="pyuiw",
            formatter_class=argparse.RawTextHelpFormatter,
            description=Version + __doc__,
        )
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
            default="<%(py)s_ui.py>",
            metavar="FILE",
            help="write generated code to FILE instead of stdout\n"
            "<EXP> to define a output expression \n"
            "%%(py)s for input python file name (default: <%%(py)s_ui.py>)",
        )
        self.parser.add_argument(
            "-x",
            "--execute",
            dest="execute",
            action="store_false",
            help="generate extra code to test and display the class",
        )
        self.parser.add_argument(
            "-d",
            "--debug",
            dest="debug",
            action="store_false",
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
            action="store_false",
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
        self.parser.add_argument_group(g)

        g = self.parser.add_argument_group(title="Watcher options")
        g.add_argument(
            "-w",
            "--watch",
            dest="watch",
            action="extend",
            type=str,
            default=argparse.SUPPRESS,
            nargs="*",
            help="watch files or directories",
        )
        g.add_argument(
            "-e",
            "--exclude",
            dest="exclude",
            action="extend",
            type=str,
            default=argparse.SUPPRESS,
            nargs="*",
            help="exclude files re expression",
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


if __name__ == "__main__":
    PyUIWatcherCli()
