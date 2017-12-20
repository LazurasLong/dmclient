# ui/qt/archive.py
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

"""All Qt-specific archive-related widget code."""

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QTextEdit, QVBoxLayout

from core.config import LICENSE_NAGGING
from ui.widgets.add_archive import Ui_ArchiveViewer
from ui.widgets.license_confirmation import Ui_LicenseConfirmationDialog


class LicenseViewer(QDialog):
    def __init__(self, parent, license_text):
        QDialog.__init__(self, parent)
        self.setWindowTitle("License agreement")
        vlayout = QVBoxLayout(self)
        text_edit = QTextEdit(self)
        text_edit.setReadOnly(True)
        text_edit.setText(license_text)
        vlayout.addWidget(text_edit)
        button_box = QDialogButtonBox(self)
        button_box.addButton(QDialogButtonBox.Ok)
        vlayout.addWidget(button_box)
        button_box.accepted.connect(self.accept)


class LicenseConfirmationDialog(QDialog, Ui_LicenseConfirmationDialog):
    """This class is required due to a restriction in Qt:

        Users cannot interact with any other window in the same application until they close the dialog,
        either by clicking a button or by using a mechanism provided by the window system.

        -- Documentation for QMessageBox

    This is inappropriate given our requirement that users can click a "View license" button.
    """

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.label.setText(LICENSE_NAGGING)
        self.buttonBox.button(QDialogButtonBox.Ok).setText("Agree")
        self.buttonBox.button(QDialogButtonBox.Cancel).setText("Disagree")
        self.viewLicenseButton.clicked.connect(self.on_view_license)

    def on_view_license(self):
        dlg = LicenseViewer(self, "FIXME: License Text!")
        dlg.exec_()


class ArchiveDialog(QDialog, Ui_ArchiveViewer):
    def __init__(self, parent, archive_meta):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.buttonBox.button(QDialogButtonBox.Ok).setText("Add Archive"),
        self.buttonBox.accepted.connect(self.on_add_archive)
        self._bind(archive_meta)
        has_isbn = archive_meta["isbn"]
        self.isbnLabel.setVisible(has_isbn)
        self.isbn.setVisible(has_isbn)

    def _bind(self, d):
        for k, v in d.items():
            w = getattr(self, k)
            w.setText(v)

    def on_add_archive(self):
        dlg = LicenseConfirmationDialog(self)
        dlg.accepted.connect(self.accept)
        # Do not hook up the `rejected' signal (give user a chance to re-view)
        dlg.exec()
