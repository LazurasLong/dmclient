from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QValidator
from PyQt5.QtWidgets import QDialog

from ui.widgets.game.system_editor import Ui_SystemEditor


class SystemIDValidator(QValidator):
    def __init__(self, game_system_manager, parent=None):
        super().__init__(parent)
        self.game_system_manager = game_system_manager

    def validate(self, input, pos):
        if input.isalpha() and input.isupper():
            return QValidator.Acceptable, input, pos
        if input.isalpha():
            return QValidator.Intermediate, input, pos
        return QValidator.Invalid, input, pos

    def fixup(self, string):
        return string.upper()


class SystemPropertiesEditor(QDialog, Ui_SystemEditor):
    def __init__(self, game_system, id_validator, parent=None):
        super().__init__(parent)
        self.game_system = game_system
        self.setupUi(self)
        if game_system.name:
            title = "Edit {}".format(game_system.name)
        else:
            title = "Edit new game system"
        self.setWindowTitle(title)
        self.game_system_id.setValidator(id_validator)
        self.name.setText(game_system.name)
        self.game_system_id.setText(game_system.id)
        self.author.setText(game_system.author)
        self.creation_date.setDate(game_system.creation_date)
        # self.revision_date.setText(datetime.now())
        self.description = game_system.description

        self.name.editingFinished.connect(self._set_name)

    @pyqtSlot()
    def _set_name(self):
        self.game_system.name = self.name.text()
