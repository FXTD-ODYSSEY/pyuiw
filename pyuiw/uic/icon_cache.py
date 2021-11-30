#!/usr/bin/env python
# This file is part of the PySide project.
#
# Copyright (C) 2011 Nokia Corporation and/or its subsidiary(-ies).
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
import os.path

# Import local modules
from pyuiw.uic.Compiler.qtproxies import QtWidgets


standard_icons = [
    "SP_ArrowBack",
    "SP_ArrowDown",
    "SP_ArrowForward",
    "SP_ArrowLeft",
    "SP_ArrowRight",
    "SP_ArrowUp",
    "SP_BrowserReload",
    "SP_BrowserStop",
    "SP_CommandLink",
    "SP_ComputerIcon",
    "SP_CustomBase",
    "SP_DesktopIcon",
    "SP_DialogApplyButton",
    "SP_DialogCancelButton",
    "SP_DialogCloseButton",
    "SP_DialogDiscardButton",
    "SP_DialogHelpButton",
    "SP_DialogNoButton",
    "SP_DialogOkButton",
    "SP_DialogOpenButton",
    "SP_DialogResetButton",
    "SP_DialogSaveButton",
    "SP_DialogYesButton",
    "SP_DirClosedIcon",
    "SP_DirHomeIcon",
    "SP_DirIcon",
    "SP_DirLinkIcon",
    "SP_DirLinkOpenIcon",
    "SP_DirOpenIcon",
    "SP_DockWidgetCloseButton",
    "SP_DriveCDIcon",
    "SP_DriveDVDIcon",
    "SP_DriveFDIcon",
    "SP_DriveHDIcon",
    "SP_DriveNetIcon",
    "SP_FileDialogBack",
    "SP_FileDialogContentsView",
    "SP_FileDialogDetailedView",
    "SP_FileDialogEnd",
    "SP_FileDialogInfoView",
    "SP_FileDialogListView",
    "SP_FileDialogNewFolder",
    "SP_FileDialogStart",
    "SP_FileDialogToParent",
    "SP_FileIcon",
    "SP_FileLinkIcon",
    "SP_LineEditClearButton",
    "SP_MediaPause",
    "SP_MediaPlay",
    "SP_MediaSeekBackward",
    "SP_MediaSeekForward",
    "SP_MediaSkipBackward",
    "SP_MediaSkipForward",
    "SP_MediaStop",
    "SP_MediaVolume",
    "SP_MediaVolumeMuted",
    "SP_MessageBoxCritical",
    "SP_MessageBoxInformation",
    "SP_MessageBoxQuestion",
    "SP_MessageBoxWarning",
    "SP_TitleBarCloseButton",
    "SP_TitleBarContextHelpButton",
    "SP_TitleBarMaxButton",
    "SP_TitleBarMenuButton",
    "SP_TitleBarMinButton",
    "SP_TitleBarNormalButton",
    "SP_TitleBarShadeButton",
    "SP_TitleBarUnshadeButton",
    "SP_ToolBarHorizontalExtensionButton",
    "SP_ToolBarVerticalExtensionButton",
    "SP_TrashIcon",
    "SP_VistaShield",
]


class IconCache(object):
    """Maintain a cache of icons.  If an icon is used more than once by a GUI
    then ensure that only one copy is created.
    """

    def __init__(self, object_factory, qtgui_module):
        """Initialise the cache."""

        self._object_factory = object_factory
        self._qtgui_module = qtgui_module
        self._base_dir = ""
        self._cache = []

    def set_base_dir(self, base_dir):
        """Set the base directory to be used for all relative filenames."""

        self._base_dir = base_dir

    def get_icon(self, iconset):
        """Return an icon described by the given iconset tag."""
        icon_name = iconset.attrib.get("theme")
        if icon_name in standard_icons:
            return QtWidgets.QApplication.style().standardIcon(
                getattr(QtWidgets.QStyle, icon_name)
            )
        iset = _IconSet(iconset, self._base_dir)

        try:
            idx = self._cache.index(iset)
        except ValueError:
            idx = -1

        if idx >= 0:
            # Return the icon from the cache.
            iset = self._cache[idx]
        else:
            # Follow uic's naming convention.
            name = "icon"
            idx = len(self._cache)

            if idx > 0:
                name += str(idx)

            icon = self._object_factory.createQObject(
                "QIcon", name, (), is_attribute=False
            )
            iset.set_icon(icon, self._qtgui_module)
            self._cache.append(iset)

        return iset.icon


class _IconSet(object):
    """An icon set, ie. the mode and state and the pixmap used for each."""

    def __init__(self, iconset, base_dir):
        """Initialise the icon set from an XML tag."""

        # Set the pre-Qt v4.4 fallback (ie. with no roles).
        self._fallback = self._file_name(iconset.text, base_dir)
        self._use_fallback = True

        # Parse the icon set.
        self._roles = {}

        for i in iconset:
            file_name = i.text
            if file_name is not None:
                file_name = self._file_name(file_name, base_dir)

            self._roles[i.tag] = file_name
            self._use_fallback = False

        # There is no real icon yet.
        self.icon = None

    @staticmethod
    def _file_name(fname, base_dir):
        """Convert a relative filename if we have a base directory."""

        fname = fname.replace("\\", "\\\\")

        if base_dir != "" and fname[0] != ":" and not os.path.isabs(fname):
            fname = os.path.join(base_dir, fname)

        return fname

    def set_icon(self, icon, qtgui_module):
        """Save the icon and set its attributes."""

        if self._use_fallback:
            icon.addFile(self._fallback)
        else:
            for role, pixmap in self._roles.items():
                if role.endswith("off"):
                    mode = role[:-3]
                    state = qtgui_module.QIcon.Off
                elif role.endswith("on"):
                    mode = role[:-2]
                    state = qtgui_module.QIcon.On
                else:
                    continue

                mode = getattr(qtgui_module.QIcon, mode.title())

                if pixmap:
                    icon.addPixmap(qtgui_module.QPixmap(pixmap), mode, state)
                else:
                    icon.addPixmap(qtgui_module.QPixmap(), mode, state)

        self.icon = icon

    def __eq__(self, other):
        """Compare two icon sets for equality."""

        if not isinstance(other, type(self)):
            return NotImplemented

        if self._use_fallback:
            if other._use_fallback:
                return self._fallback == other._fallback

            return False

        if other._use_fallback:
            return False

        return self._roles == other._roles
