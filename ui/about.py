# ui/about.py
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

import webbrowser

from PyQt5.QtWidgets import *

from core.config import *
import ui.widgets

# lazily load about dialog
from ui.widgets.about import Ui_aboutDlg

_dialog = None


def show():
    global _dialog
    if not _dialog:
        _dialog = _AboutDialog()
    _dialog.show()


class _AboutDialog(QDialog, Ui_aboutDlg):
    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)
        self.setWindowTitle("About")
        self.appName.setText(APP_NAME)
        font = self.appName.font()
        font.setPointSize(24)
        self.appName.setFont(font)
        self.versionAndCodename.setText("Version %s (%s)" % (APP_VERSION, APP_VERSION_NAME))
        self.buildAndDate.setText("Build %s (%s)" % (APP_BUILD, APP_BUILD_DATE))
        self.copyright.setText(copyright)
        self.donate.clicked.connect(lambda: webbrowser.open(DONATE_URL))
