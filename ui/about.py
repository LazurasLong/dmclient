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
_dialog = None


def show():
    global _dialog
    if not _dialog:
        _dialog = _AboutDialog()
    _dialog.show()


class _AboutDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.form = ui.widgets.about.Ui_aboutDlg()
        self.form.setupUi(self)
        self.setWindowTitle("About")
        self.form.appName.setText(APP_NAME)
        font = self.form.appName.font()
        font.setPointSize(24)
        self.form.appName.setFont(font)
        self.form.versionAndCodename.setText("Version %s (%s)" % (APP_VERSION, APP_VERSION_NAME))
        self.form.buildAndDate.setText("Build %s (%s)" % (APP_BUILD, APP_BUILD_DATE))
        self.form.copyright.setText(copyright)
        self.form.donate.clicked.connect(lambda: webbrowser.open(DONATE_URL))
