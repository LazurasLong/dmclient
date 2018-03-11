# ui/tools.py
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

"""This module implements functionality from dmclient's tools menu.

.. todo ::
    Roller: Hook up contextual enter/escape key presses properly.

"""

from functools import partial  # using fun things.
from random import randint

import pyparsing  # Ugh, trash dice api.
from dice import roll
from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *

from ui.widgets.results import Ui_ResultsDialog
from ui.widgets.roller import Ui_RollerControls


__all__ = ["DiceRollerDialog", "Die", "DiceController"]


class DiceRollerDialog(QDialog, Ui_ResultsDialog):
    def __init__(self, dice_controller):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Dice Roller")
        help_dialog = self.help_dialog = QDialog(self)
        help_dialog.setWindowTitle("Dice Roller Help")
        bb = QDialogButtonBox(QDialogButtonBox.Ok, help_dialog)
        help_text = QLabel("TODO: Implement help text!", help_dialog)
        layout = QVBoxLayout(help_dialog)
        layout.addWidget(help_text)
        layout.addWidget(bb)
        bb.accepted.connect(help_dialog.accept)

        self.bb.button(QDialogButtonBox.Reset).clicked.connect(self.reset)
        self.bb.button(QDialogButtonBox.Help).clicked.connect(help_dialog.show)

        roller_controls = QWidget(self)
        form = self.roller_form = Ui_RollerControls()
        form.setupUi(roller_controls)

        form.submit.clicked.connect(form.invalidSyntaxWarning.hide)
        form.submit.clicked.connect(
            lambda: dice_controller.roll_query(form.rollQuery.text()))
        form.rollQuery.textChanged.connect(form.invalidSyntaxWarning.hide)

        dice_controller.newResult.connect(self.history.appendPlainText)
        dice_controller.syntaxError.connect(form.invalidSyntaxWarning.show)
        grid = QGridLayout(form.rollerGrid)
        for i, die in enumerate(dice_controller.dice):
            widget = QWidget()
            counter = QSpinBox(widget)
            counter.setValue(1)
            grid.addWidget(counter, i, 0)
            die_button = QPushButton(widget)
            die_button.setIcon(die.icon)
            grid.addWidget(die_button, i, 1)
            plus = QLabel(widget)
            plus.setTextFormat(Qt.RichText)
            plus.setText(
                '<html><head/><body><p><span style="font-size:12pt;">+</span></p></body></html>')
            grid.addWidget(plus, i, 2)
            modifier = QSpinBox(widget)
            modifier.setRange(-1024, 1024)
            grid.addWidget(modifier, i, 3)

            def _on_roll(die, count, mod):
                form.invalidSyntaxWarning.hide()
                dice_controller.roll(die, count(), mod())
                # HACK! ... but is this how it's done in Qt?!
                scroll_bar = self.history.verticalScrollBar()
                scroll_bar.setValue(scroll_bar.maximum())

            die_button.clicked.connect(
                partial(_on_roll, die, partial(counter.value),
                        partial(modifier.value)))
        self.layout.insertWidget(0, roller_controls)

        self.adjustSize()
        form.invalidSyntaxWarning.hide()

    def reset(self):
        self.history.clear()
        self.roller_form.invalidSyntaxWarning.hide()


class Die:
    __slots__ = ["d", "icon"]

    def __init__(self, d):
        self.d = d
        self.icon = QIcon(":/icons/dice/d{}.png".format(d))


class DiceController(QObject):
    newResult = pyqtSignal(str)
    syntaxError = pyqtSignal()

    standard_array = [20, 12, 10, 8, 6, 4, 100]

    def __init__(self, dice_d=standard_array, parent=None):
        """

        :param dice_d: List of integers of dice to use.
        """
        super().__init__(parent)
        self.dice = [Die(d) for d in dice_d]

    def roll(self, die, count, modifier):
        assert 0 <= count
        result = randint(count, count * die.d) + count * modifier
        self.newResult.emit(
            "{}d{}+{} = {}".format(count, die.d, modifier, result))

    def roll_query(self, text):
        if not text:
            return
        try:
            # Hack: tack on +0 to force evaluation
            # (Their API docs are complete garbage)
            self.newResult.emit("{} = {}".format(text, roll(text)))
        except pyparsing.ParseException:  # Ugh, trash dice api.
            self.syntaxError.emit()


class Names:
    def __init__(self):
        self.first = []
        self.last = []


class NameGenParser:
    def __init__(self):
        pass

    def parse(self, f):
        names = Names()
        target = names.first
        for line in [line.strip() for line in f]:
            if line == "---":
                target = names.last
            else:
                target.append(line)
        return names
