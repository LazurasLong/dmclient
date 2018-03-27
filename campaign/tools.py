from random import randint, choice

import os
import pyparsing  # Ugh, trash dice api.
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon
from dice import roll

from core import filters
from core.controller import QtViewController
from ui import get_open_filename


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

    def bind(self, view):
        pass

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
        except pyparsing.ParseException:
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


class NameGenController(QtViewController):
    groupsChanged = pyqtSignal(list)
    newResult = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.groups = []
        self.current_group_nb = -1
        self.current_gender = male
        self.view = None

    def bind(self, view):
        super().bind(view)

        view.form.name_groups.activated.connect(self.on_cb_activated)
        view.form.male_names.clicked.connect(lambda: self.set_current_gender(male))
        view.form.female_names.clicked.connect(lambda: self.set_current_gender(female))
        view.form.generate.clicked.connect(self.on_generate)

        self.groupsChanged.connect(view.groups_changed)
        self.groupsChanged.emit(self.groups)  # FIXME hack
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
