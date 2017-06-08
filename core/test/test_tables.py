# core/test/test_tables.py
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

import random

import numpy.random
import pytest

from core.tables import DiscreteTable, WeightedTable


@pytest.fixture(scope="function")
def fixedseed():
    random.seed(1)
    numpy.random.seed(42)  # chosen arbitrarily


def test_discrete_table(fixedseed):
    t = DiscreteTable("footable")
    assert t.name == "footable"

    t.add("foo")
    t.add("bar")
    t.add("baz")
    assert t.choice() == "foo"
    assert t.choice() == "baz"
    assert t.choice() == "foo"
    assert t.choice() == "bar"


def test_weighted_table_add(fixedseed):
    t = WeightedTable("footable")
    assert t.name == "footable"

    t.add("foo")
    t.add("bar")
    t.add("baz")
    assert t.choice() == "foo"
    assert t.choice() == "baz"
    assert t.choice() == "foo"
    assert t.choice() == "bar"


def test_weighted_table_add(fixedseed):
    wt = WeightedTable("footable")
    wt.add_weighted('a', 0.1)
    wt.add_weighted('b', 0.1)
    assert wt.choice() == 'a'
    assert wt.choice() == 'b'
    assert wt.choice() == 'b'
    assert wt.choice() == 'b'
    assert wt.choice() == 'a'
