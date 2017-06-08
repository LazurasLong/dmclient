# ui/preferences.py
# Copyright (C) 2017 Alex Mair. All rights reserved.
# This file is part of dmclient.
#
# dmclient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# dmclient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with dmclient.  If not, see <http://www.gnu.org/licenses/>.
#

from PyQt5.QtWidgets import QDialog

from core.config import HAS_EXTERNAL_UPDATER
from ui.widgets.preferences import Ui_PreferencesDialog


def show_preferences(parent):
    dlg = _AppPreferencesDialog(parent)
    dlg.show()
    dlg.raise_()


class _AppPreferencesDialog(QDialog, Ui_PreferencesDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setSizeGripEnabled(False)
        self.updateSection.setVisible(not HAS_EXTERNAL_UPDATER)
