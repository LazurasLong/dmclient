from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog

from campaign import Player
from ui.widgets.player.new import Ui_NewPlayerDialog


class NewPlayerDialog(QDialog):
    playerAccepted = pyqtSignal(Player)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.form = Ui_NewPlayerDialog()
        self.form.setupUi(self)

    def accept(self):
        player = Player(name=self.form.name.text(), description="")
        self.playerAccepted.emit(player)
        super().accept()
