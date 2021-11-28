# -*- coding: utf-8 -*-
"""
Command Line Watcher for auto compile Qt ui to python file.

Usage Example:
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
import copy
from functools import partial
from io import open
import os
from pathlib import Path
import signal
import subprocess
import sys


FILE = Path(__file__)
DIR = FILE.parent
signal.signal(signal.SIGINT, signal.SIG_DFL)

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


class CliBase(object):
    def __init__(self):
        self.output = ""
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
            exp = exp[1:-1] % {"py_name": ui_file.stem, "py_dir": ui_file.parent}
            exp = os.path.abspath(exp)
        return exp

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
            return

        opts = copy.deepcopy(self.opts)
        opts.output = self.parse_exp(self.opts.output, ui_file)
        ui_file = str(ui_file.absolute())
        print(opts, ui_file)

        # FIXME: some ui file output empty
        invoke(Driver(opts, ui_file))

        subprocess.call([sys.executable, "-m", "black", opts.output])
        # FIXME: isort permission error when watching
        # args = [sys.executable,"-m","isort",opts.output]
        # subprocess.call(args)
        # QtCore.QTimer.singleShot(0, partial(subprocess.call,args))

        print("output: ", opts.output)

    def parse(self):
        self.opts, args = self.parser.parse_known_args()
        self.output = self.opts.output

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
        for ui_file in paths:
            self.parse_single_ui([ui_file])

        watcher.fileChanged.connect(self.on_file_change)
        app.exec_()

    def on_file_change(self, ui_file):
        # QtCore.QTimer.singleShot(0, partial(self.parse_single_ui,[ui_file]))
        self.parse_single_ui([ui_file])


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
        default_exp = r"<%(py_dir)s/%(py_name)s_ui.py>"
        self.parser.add_argument(
            "-o",
            "--output",
            dest="output",
            action="store",
            type=str,
            default=default_exp,
            metavar="FILE",
            help="write generated code to FILE instead of stdout\n"
            f"<EXP> to define a output expression (default: {default_exp})\n"
            r"%(py_dir)s - input python directory path\n"
            r"%(py_name)s - input python file name\n",
        )
        self.parser.add_argument(
            "-x",
            "--execute",
            dest="execute",
            action="store_false",
            default=False,
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
            action="store_false",
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
