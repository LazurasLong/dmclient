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

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from ui.widgets.namegen import Ui_NameGenControls
from ui.widgets.results import Ui_ResultsDialog
from ui.widgets.roller import Ui_RollerControls


class DiceRollerDialog(QDialog, Ui_ResultsDialog):
    def __init__(self):
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

        self.roller_controls = QWidget(self)
        form = self.roller_form = Ui_RollerControls()
        form.setupUi(self.roller_controls)

        form.submit.clicked.connect(form.invalidSyntaxWarning.hide)

    def set_controller(self, dice_controller):  # FIXME relic of shite arch
        form = self.roller_form
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
            plus.setText('<html><head/><body><p>'
                         '<span style="font-size:12pt;">+</span>'
                         '</p></body></html>')
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
        self.layout.insertWidget(0, self.roller_controls)

        self.adjustSize()
        form.invalidSyntaxWarning.hide()

    def reset(self):
        self.history.clear()
        self.roller_form.invalidSyntaxWarning.hide()


class NameGenDialog(QDialog, Ui_ResultsDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Name generator")
        name_controls = QWidget(self)
        self.bb.button(QDialogButtonBox.Help).clicked.connect(self.history.clear)
        form = self.form = Ui_NameGenControls()
        form.setupUi(name_controls)
        self.layout.insertWidget(0, name_controls)

    def groups_changed(self, groups):
        name_groups = self.form.name_groups
        name_groups.clear()
        for group in groups:
             name_groups.addItem(group.set_name)
        enabled = 0 < len(groups)
        self.form.male_names.setEnabled(enabled)
        self.form.female_names.setEnabled(enabled)
        self.form.generate.setEnabled(enabled)
        name_groups.insertSeparator(name_groups.count())
        name_groups.addItem("Import...")

    def results_changed(self, results):
        self.history.clear()
        for result in results:
            self.history.appendPlainText(result)
