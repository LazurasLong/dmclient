# ui/__init__.py
# Copyright (C) 2018 Alex Mair. All rights reserved.
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
import os

from PyQt5.QtWidgets import *

from core import filters
from core.config import appconfig
from ui.widgets.loading import Ui_LoadingWidget

__all__ = [
    "display_error",
    "display_info",
    "display_warning",
    "LoadingWidget",
    "LoadingDialog",
]


def display_error(parent, msg, title="Error"):
    """Display an error message in a message box."""
    QMessageBox.critical(parent, title, msg)


def display_warning(parent, msg, title="Warning"):
    QMessageBox.warning(parent, title, msg)


def display_info(parent, msg, title="Information"):
    QMessageBox.information(parent, title, msg)


def _qfiledialog(f, parent, title, dir_=None, filter_=filters.any,
                 recent_key=None):
    if recent_key and not dir_:
        try:
            path = appconfig().recent_dirs[recent_key]
        except KeyError as e:
            path = os.path.expanduser('~')
    else:
        path = dir_
    # The static functions are better than the ctor because they use native
    # widgets, so we should deduce the recent dir from the path
    val = f(parent, title, path, filter_)
    if recent_key and val:
        if isinstance(val, tuple):
            recent_path = val[0]
        else:
            recent_path = val
        appconfig().recent_dirs[recent_key] = os.path.dirname(recent_path)
    return val


def get_open_filename(parent, title, filter_=filters.any, dir_=None,
                      recent_key=None):
    return _qfiledialog(QFileDialog.getOpenFileName, parent,
                        title, dir_, filter_, recent_key)[0]


def get_open_filenames(parent, title, filter_=filters.any, dir_=None,
                       recent_key=None):
    return _qfiledialog(QFileDialog.getOpenFileNames, parent,
                        title, dir_, filter_, recent_key)


def get_save_filename(parent, title, filter_=filters.any, dir_=None,
                      recent_key=None):
    return _qfiledialog(QFileDialog.getSaveFileName, parent, title, dir_,
                        filter_, recent_key)[0]


def get_polar_response(parent, msg, affirmative, title="Question",
                       dissenting="Cancel"):
    """
    Ask the user a question and return their response as ``True`` for "yes" and
    ``False`` for "no".

    :param parent: Parent window or dialog.
    :param msg: The message to display.
    :param affirmative: The text to show on the "Yes" button. Must be specified.
    :param title: The message box title.
    :param dissenting: The text to show on the "No" button; "Cancel" by default.
    :return: ``True`` if the user selected the affirmative, ``False`` otherwise.
    """
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
    """

    :return:  A QWidget suitable as a "spacer" in toolbars and the like.
    """
    widget = QWidget(parent)
    widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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


class LoadingWidget(QWidget, Ui_LoadingWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.loading_label.setVisible(False)

    def setText(self, text):
        self.loading_label.setVisible(text != "")
        self.loading_label.setText(text)

    def update_progress(self, percent, text=None):
        self.progressBar.setValue(percent)
        if text:
            self.setText(text)


class LoadingDialog(QDialog):
    def __init__(self, parent=None, loading_text=""):
        super().__init__(parent)
        self.setModal(True)
        self.task = None
        widget = self.widget = LoadingWidget(self)
        widget.setText(loading_text)
        layout = QVBoxLayout()
        layout.addWidget(widget)
        self.setLayout(layout)
        self.setWindowTitle(loading_text if loading_text else "Loading...")

    def set_task(self, task):
        self.task = task
        self.update_progress(0)

    def set_task(self, task):
        self.task = task
        self.update_progress(0)

    def update_progress(self, percent):
        self.widget.update_progress(percent)
