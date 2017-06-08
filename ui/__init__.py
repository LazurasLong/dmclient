# ui/__init__.py
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

from PyQt5.QtWidgets import QMessageBox, QFileDialog
from PyQt5.QtWidgets import QWidget

from core import filters
from core.config import APP_PATH


def display_error(parent, msg, title="Error"):
    """Display an error message in a message box."""
    QMessageBox.critical(parent, title, msg)


def display_warning(parent, msg, title="Warning"):
    QMessageBox.warning(parent, title, msg)


def display_info(parent, msg, title="Information"):
    QMessageBox.information(parent, title, msg)


def get_open_filename(parent, title, filter_=filters.any, dir_="test"):
    return QFileDialog.getOpenFileName(parent, title, dir_, filter_)[0]


def get_open_filenames(parent, title, filter_=filters.any, dir_=APP_PATH):
    return QFileDialog.getOpenFileNames(parent, title, dir_, filter_)[0]


def get_save_filename(parent, title, filter_=filters.any, dir_=APP_PATH):
    return QFileDialog.getSaveFileName(parent, title, dir_, filter_)[0]


def get_polar_response(parent, msg, affirmative, title="Question", dissenting="Cancel"):
    assert affirmative != "", "Affirmative text must always be explicitly specified!"
    msgbox = QMessageBox(parent)
    msgbox.setWindowTitle(title)
    msgbox.setText(msg)
    msgbox.setIcon(QMessageBox.Question)
    msgbox.addButton(dissenting, QMessageBox.NoRole)
    affirmative_button = msgbox.addButton(affirmative, QMessageBox.YesRole)
    msgbox.exec_()
    if msgbox.clickedButton() == affirmative_button:
        return True
    return False


def spacer_widget(parent=None):
    widget = QWidget(parent)
    return widget


class ResourceDialogManager:  # FIXME: good idea, crap name
    def __init__(self, model, dialogcls, dialog_parent):
        self._model = model
        self._dialogcls = dialogcls
        self._parent = dialog_parent
        # map of asset id -> dialog instance
        self._open_dialogs = {}

    def on_show(self, qmodelindex):
        """Show or create a dialog for a given id."""
        dialog = self._create_dialog(qmodelindex)
        """
        try:
            dialog = self._open_dialogs[id_]
        except KeyError:
            dialog = self._create_dialog(id_)
            self._open_dialogs[id_] = dialog
        """
        dialog.show()
        dialog.raise_()

    def on_dialog_closed(self, dialog, id):
        print("on_dialog_closed({})".format(id))
        return
        did = dialog.id
        try:
            del self._open_dialogs[did]
        except KeyError:
            log.warning("Requested to close a dialog for which I am unfamiliar")

    def _create_dialog(self, index):
        item = self._model.data(index)
        dialog = self._dialogcls(item, self._parent)
        dialog.finished.connect(lambda res: self.on_dialog_closed(dialog, res))
        return dialog

    def _get_id_for_index(self, qmodelindex):
        raise NotImplementedError
