# core/tables.py
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

"""This module provides probability tables, useful for encounter tables, loot
tables, etc.

"""

import random

import numpy
import numpy.random


class Table:
    def __init__(self, name=""):
        """

        :param name:  The title of the table.
        """
        self.name = name
        self._rows = []

    def add(self, row_name):
        raise NotImplementedError("abstract method")

    def clear(self):
        self._rows.clear()


class DiscreteTable(Table):
    def add(self, row_name):
        self._rows.append(row_name)

    def choice(self):
        """Given a probability ``f`` between ``0.0`` and ``1.0``, return
        a table entry -- either a string or a ``Table``.

        """
        return random.choice(self._rows)


class WeightedTable(Table):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._row_weights = []
        self._row_probs = None

    def add(self, row_name):
        self.add_weighted(row_name, 1.0)

    def add_weighted(self, name, weight):
        self._rows.append(name)
        self._row_weights.append(weight)

    def choice(self):
        if not self._row_probs:
            total = sum(self._row_weights)
            self._row_probs = [w / total for w in self._row_weights]
        return numpy.random.choice(self._rows, p=self._row_probs)

    def clear(self):
        super().clear()
        self._row_weights = []
        self._row_probs = None

