# This file is part of the PySide project.
#
# Copyright (C) 2009-2011 Nokia Corporation and/or its subsidiary(-ies).
# Copyright (C) 2010 Riverbank Computing Limited.
# Copyright (C) 2009 Torsten Marek
#
# Contact: PySide team <pyside@openbossa.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# version 2 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
# 02110-1301 USA

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
import os
import sys

# Import local modules
from pyuiw.uic.Compiler import qtproxies
from pyuiw.uic.Compiler.indenter import createCodeIndenter
from pyuiw.uic.Compiler.indenter import getIndenter
from pyuiw.uic.Compiler.indenter import write_code
from pyuiw.uic.Compiler.misc import write_import
from pyuiw.uic.Compiler.qobjectcreator import CompilerCreatorPolicy
from pyuiw.uic.properties import Properties
from pyuiw.uic.uiparser import UIParser


class UICompiler(UIParser):
    def __init__(self):
        UIParser.__init__(
            self,
            qtproxies.QtCore,
            qtproxies.QtGui,
            qtproxies.QtWidgets,
            CompilerCreatorPolicy(),
        )

    def reset(self):
        qtproxies.i18n_strings = []
        UIParser.reset(self)

    def setContext(self, context):
        qtproxies.i18n_context = context

    def createToplevelWidget(self, classname, widgetname):
        indenter = getIndenter()
        indenter.level = 0

        is_Qt = os.getenv("pyuiw_isUseQt", "true")
        is_Qt = True if is_Qt == "true" else False
        module = os.getenv("pyuiw_QtModule", "PySide2")
        module = "Qt" if is_Qt else module
        indenter.write("from %s import QtCore" % module)
        indenter.write("from %s import QtGui" % module)
        indenter.write("from %s import QtWidgets" % module)
        if is_Qt:
            indenter.write("from Qt import QtCompat")

        indenter.write("")

        indenter.write("class Ui_%s(object):" % self.uiname)
        indenter.indent()
        indenter.write("def setupUi(self, %s):" % widgetname)
        indenter.indent()
        w = self.factory.createQObject(
            classname, widgetname, (), is_attribute=False, no_instantiation=True
        )
        w.baseclass = classname
        w.uiclass = "Ui_%s" % self.uiname
        return w

    def setDelayedProps(self):
        write_code("")
        write_code("self.retranslateUi(%s)" % self.toplevelWidget)
        UIParser.setDelayedProps(self)

    def finalize(self):
        indenter = getIndenter()
        indenter.level = 1
        indenter.write("")
        indenter.write("def retranslateUi(self, %s):" % self.toplevelWidget)
        indenter.indent()

        if qtproxies.i18n_strings:
            for s in qtproxies.i18n_strings:
                indenter.write(s)
        else:
            indenter.write("pass")

        indenter.dedent()
        indenter.dedent()

        # Make a copy of the resource modules to import because the parser will
        # reset() before returning.
        self._resources = self.resources

    def compileUi(self, input_stream, output_stream, from_imports):
        createCodeIndenter(output_stream)
        w = self.parse(input_stream)

        indenter = getIndenter()
        indenter.write("")

        self.factory._cpolicy._writeOutImports()

        for res in self._resources:
            write_import(res, from_imports)

        return {
            "widgetname": str(w),
            "uiclass": w.uiclass,
            "baseclass": w.baseclass,
        }
