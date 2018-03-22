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
from random import randint, choice

import os
import pyparsing  # Ugh, trash dice api.
from dice import roll
from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *

from core import filters
from ui import get_open_filename
from ui.widgets.namegen import Ui_NameGenControls
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
        self.set_name = ""
        self.male = []
        self.female = []
        self.last = []

    def _name(self, target):
        return "{} {}".format(choice(target), choice(self.last))

    def male_name(self):
        return self._name(self.male)

    def female_name(self):
        """Returns a randomly generated full name."""
        return self._name(self.female)


class NameGenParser:
    def __init__(self):
        pass

    def parse(self, f):
        names = Names()
        targets = iter([names.male, names.female, names.last])
        target = next(targets)
        for line in [line.strip() for line in f]:
            if line == "---":
                target = next(targets)
                continue
            target.append(line)
        return names


male = 0
female = 1


class NameGenController(QObject):
    groupsChanged = pyqtSignal(list)
    newResult = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.groups = []
        self.current_group_nb = -1
        self.current_gender = male
        self.view = None

    def init_view(self, view):
        self.view = view

        view.form.name_groups.activated.connect(self.on_cb_activated)
        view.form.male_names.clicked.connect(lambda: self.set_current_gender(male))
        view.form.female_names.clicked.connect(lambda: self.set_current_gender(female))
        view.form.generate.clicked.connect(self.on_generate)

        self.groupsChanged.connect(view.groups_changed)
        self.groupsChanged.emit(self.groups)
        self.newResult.connect(view.results_changed)

    @property
    def current_group(self):
        # stupid
        assert self.current_group_nb != -1
        return self.groups[self.current_group_nb]

    def set_current_gender(self, gender):
        self.current_gender = gender

    def set_group(self, group_nb):
        self.current_group_nb = group_nb

    @pyqtSlot(int)
    def on_cb_activated(self, i):
        name_groups = self.view.form.name_groups
        if i + 1 == name_groups.count():
            path = get_open_filename(self.view, "Import name generator",
                                     filter_=filters.txt)
            if not path:
                name_groups.setCurrentIndex(0)
                return
            parser = NameGenParser()
            with open(path) as f:
                names = parser.parse(f)
                # FIXME
                names.set_name = os.path.splitext(os.path.basename(path))[0]
                self.groups.append(names)
                self.groupsChanged.emit(self.groups)
                new_group_i = len(self.groups) - 1
                self.current_group_nb = new_group_i
                self.view.form.name_groups.setCurrentIndex(new_group_i)
        elif i == name_groups.count():
            # separator
            pass
        else:
            self.set_group(i)

    @pyqtSlot()
    def on_generate(self):
        if self.current_gender == male:
            target = self.current_group.male_name
        else:
            target = self.current_group.female_name
        results = list([target() for _ in range(10)])
        self.newResult.emit(results)


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
