# test/qtmodeltest.py
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

import unittest  # FIXME: get rid of old unittest-style tests
from itertools import product

import pytest
from PyQt5.QtCore import QAbstractListModel, QDate, QDateTime, QModelIndex, \
    QVariant, Qt
from dateutil.parser import parse as dtparse
from marshmallow import fields

import core.hacks
from model.qt import AbstractQtModel, ListModel, ReadOnlyListModel, \
    SchemaTableModel
from model.schema import Schema

core.hacks.show_recursive_relationships = True
core.hacks.install_qt_reprs()


class SignalSentinel:

    def __init__(self, signal=None):
        self.count = 0
        self.last_args = ()
        if signal:
            signal.connect(self)

    def reset(self):
        self.count = 0
        self.last_args = ()

    def __call__(self, *args):
        self.last_args = args
        self.count += 1

    def was_signalled(self):
        return 0 < self.count


class DummyModel(AbstractQtModel, QAbstractListModel):
    """Keep ListModel out of this for now..."""
    def __init__(self, itemcls, data, parent=None):
        AbstractQtModel.__init__(self, itemcls, data)
        QAbstractListModel.__init__(self, parent)


class TestAbstractQtModelPython(unittest.TestCase):
    def setUp(self):
        self.model = DummyModel(lambda x=0: int(x), [])
        self.sentinel = SignalSentinel()

    def test_index(self):
        self.assertRaises(ValueError, self.model.index_, 1)
        self.model.append(1)
        self.assertEquals(self.model.index_(1), 0)
        self.model.append(2)
        self.model.append(1)
        self.assertEquals(self.model.index_(1, 1), 2)

    def test_len(self):
        self.assertEquals(len(self.model), 0)
        self.model.append(1)
        self.assertEquals(len(self.model), 1)
        self.model.append(2)
        self.assertEquals(len(self.model), 2)

    def test_remove(self):
        self.assertRaises(ValueError, self.model.remove, 0)

        self.model.append(0)
        self.model.append(1)
        self.model.append(0)
        self.model.remove(0)
        self.assertEqual(self.model[0], 1)
        self.assertEqual(self.model[1], 0)
        self.assertEqual(len(self.model), 2)

        self.model.remove(0)
        self.model.remove(1)
        self.assertRaises(ValueError, self.model.remove, 0)
        self.assertRaises(ValueError, self.model.remove, 1)

    def test_remove_rowsAboutToBeRemoved(self):
        self.model.rowsAboutToBeRemoved.connect(self.sentinel)

        self.model.append(0)
        self.model.remove(0)
        self.assertTrue(self.sentinel.was_signalled())
        self.assertEqual(self.sentinel.last_args, (QModelIndex(), 0, 0))
        self.sentinel.reset()

        self.assertEqual(len(self.model), 0, "sanity check")
        for i in [0, 1, 2, 2]:
            self.model.append(i)

        self.model.remove(2)
        self.assertTrue(self.sentinel.was_signalled())
        self.assertEqual(self.sentinel.last_args, (QModelIndex(), 2, 2))
        self.sentinel.reset()

        self.model.remove(2)
        self.assertTrue(self.sentinel.was_signalled())
        self.assertEqual(self.sentinel.last_args, (QModelIndex(), 2, 2))

    def test_append_signals(self):
        self.model.rowsAboutToBeInserted.connect(self.sentinel)

        self.model.append(1)
        self.assertTrue(self.sentinel.was_signalled(),
                        "rowsAboutToBeInserted did not trigger!")
        self.assertEqual(self.sentinel.last_args, (QModelIndex(), 0, 0))
        self.sentinel.reset()

        self.model.append(2)
        self.assertTrue(self.sentinel.was_signalled(),
                        "rowsAboutToBeInserted did not trigger!")
        self.assertEqual(self.sentinel.last_args, (QModelIndex(), 1, 1))


class TestAbstractQtModelQt(unittest.TestCase):
    def setUp(self):
        self.model = DummyModel(lambda x=0: int(x), [])
        self.sentinel = SignalSentinel()

    def test_insertRow_and_insertRows(self):
        self.model.insertRow(0)
        self.model[0] = 31337
        self.assertEquals(self.model.rowCount(), 1)
        self.assertEquals(self.model[0], 31337)

        self.model.insertRow(1)
        self.model[1] = 1000
        self.assertEquals(self.model.rowCount(), 2)
        self.assertEquals(len(self.model), 2)
        self.assertEquals(self.model[0], 31337)
        self.assertEquals(self.model[1], 1000)

        items = list(range(5))
        self.model.insertRows(0, len(items))
        self.assertEquals(self.model.rowCount(), 7)
        for i in items[:-1]:
            self.model[i] = i + 1
        for i, n in enumerate([1, 2, 3, 4, 0, 31337, 1000]):
            self.assertEquals(self.model[i], n, "m[%d] should be %d!" % (i, n))

    def test_qt_insertRow_signals(self):
        self.model.rowsAboutToBeInserted.connect(self.sentinel)

        self.model.insertRow(0)
        self.assertTrue(self.sentinel.was_signalled(),
                        "rowsAboutToBeInserted did not trigger!")
        self.assertEqual(self.sentinel.last_args, (QModelIndex(), 0, 0))

        self.sentinel.reset()

        self.model.insertRow(1)
        self.assertTrue(self.sentinel.was_signalled(),
                        "rowsAboutToBeInserted did not trigger!")
        self.assertEqual(self.sentinel.last_args, (QModelIndex(), 1, 1))

    def test_removeRow(self):
        self.model.append(1)
        self.model.append(31337)
        self.model.removeRow(0)
        self.assertEquals(self.model.rowCount(), 1)
        self.assertEquals(self.model[0], 31337)

    def test_qt_removeRow_signals(self):
        self.model.rowsAboutToBeRemoved.connect(self.sentinel)

        self.model.append(1)
        self.model.append(31337)

        self.model.removeRow(0)
        self.assertTrue(self.sentinel.was_signalled(),
                        "rowsAboutToBeRemoved did not trigger!")


class ListModelTests(unittest.TestCase):
    def setUp(self):
        self.model = ListModel(lambda x: int(x), [])

    def test_columnCount(self):
        self.assertEqual(self.model.columnCount(), 1)

    def test_data(self):
        self.model.append(42)
        self.model.append(31337)
        index00 = self.model.index(0, 0)
        index01 = self.model.index(0, 1)
        self.assertEqual(self.model.data(index00), 42)
        self.assertEqual(self.model.data(index01), 31337)


class MockSchema(Schema):
    field_str = fields.Str()
    field_int = fields.Int()


class ModelObject:
    def __init__(self, text="foo", number=42):
        self.field_str = text
        self.field_int = number


class SchemaTableModelPythonTests(unittest.TestCase):
    def setUp(self):
        self.model = SchemaTableModel(MockSchema, ModelObject)
        self.sentinel = SignalSentinel()

    def test_python(self):
        self.assertRaises(IndexError, lambda: self.model[0])
        self.assertEqual(len(self.model), 0)
        self.model.append(ModelObject("foo", 42))
        self.assertEqual(len(self.model), 1)
        del self.model[0]
        self.assertEqual(len(self.model), 0)
        self.assertRaises(IndexError, lambda: self.model[0])


class SchemaTableModelQtTests(unittest.TestCase):
    def setUp(self):
        self.model = SchemaTableModel(MockSchema, ModelObject)
        self.sentinel = SignalSentinel()

    def test_insertRow(self):
        self.assertEqual(self.model.rowCount(), 0)
        self.assertEqual(self.model.columnCount(QModelIndex()), 2)
        self.model.insertRow(0)
        self.assertEqual(self.model.rowCount(), 1)
        self.assertEqual(self.model.columnCount(QModelIndex()), 2)

    def test_qt_signals(self):
        self.model.dataChanged.connect(self.sentinel)
        self.model.insertRow(0)
        index = self.model.index(0, 1)
        self.assertTrue(self.model.setData(index, 1))
        self.assertTrue(self.sentinel.was_signalled())

    def test_headerData(self):
        self.assertEqual(self.model.headerData(0, Qt.Horizontal), "field_str")
        self.assertEqual(self.model.headerData(1, Qt.Horizontal), "field_int")
        for i in (0, 1):
            self.assertEqual(self.model.headerData(i, Qt.Horizontal,
                                                   role=Qt.DecorationRole),
                             QVariant())

    def test_setHeaderData(self):
        for i, role in product([0, 1, 2],
                               (Qt.DisplayRole, Qt.DecorationRole)):
            self.assertFalse(self.model.setHeaderData(i, Qt.Vertical,
                                                      "no", role=role))

        self.assertTrue(self.model.setHeaderData(0, Qt.Horizontal, "foo"))
        self.assertEqual(self.model.headerData(0, Qt.Horizontal), "foo")
        self.assertEqual(self.model.headerData(1, Qt.Horizontal), "field_int")
        for i in (0, 1):
            self.assertEqual(self.model.headerData(i, Qt.Horizontal,
                                                   role=Qt.DecorationRole),
                             QVariant())

        self.assertTrue(self.model.setHeaderData(1, Qt.Horizontal, "bar",
                                                 role=Qt.DecorationRole))
        self.assertEqual(self.model.headerData(0, Qt.Horizontal), "foo");
        self.assertEqual(self.model.headerData(1, Qt.Horizontal), "field_int")
        self.assertEqual(self.model.headerData(0, Qt.Horizontal,
                                               role=Qt.DecorationRole),
                         QVariant())
        self.assertEqual(self.model.headerData(1, Qt.Horizontal,
                                               role=Qt.DecorationRole),
                         "bar")

    def test_columnCount(self):
        self.assertEqual(self.model.columnCount(QModelIndex()), 2)

        class ThreeSchema(Schema):
            field_int = fields.Int()
            field_int2 = fields.Int()
            field_date = fields.DateTime()

        model = SchemaTableModel(ThreeSchema, object)
        self.assertEqual(model.columnCount(QModelIndex()), 3)

    def test_setData(self):
        m = self.model
        m.dataChanged.connect(self.sentinel)
        self.assertFalse(m.setData(m.index(-1, -1), -1))
        self.assertFalse(self.sentinel.was_signalled())

        self.assertFalse(m.setData(m.index(0, 0), -1))
        self.assertFalse(self.sentinel.was_signalled())

        m.insertRow(0)
        index00 = m.index(0, 0)
        index01 = m.index(0, 1)
        index11 = m.index(1, 1)

        self.assertTrue(m.setData(index00, "bar"))
        self.assertTrue(self.sentinel.was_signalled())
        self.sentinel.reset()

        self.assertTrue(m.setData(index01, 1))
        self.assertTrue(self.sentinel.was_signalled())
        self.sentinel.reset()

        self.assertFalse(m.setData(index11, -1))
        self.assertFalse(self.sentinel.was_signalled())

        supposed_data = [m.data(index00), m.data(index01)]
        self.assertEqual(supposed_data, ["bar", 1])
        self.assertEqual(m.data(index11), QVariant())


class SchemaWithBoolean(Schema):
    field1 = fields.Int()
    field_boolean = fields.Boolean()
    field2 = fields.Int()


class ThingWithBoolean:
    def __init__(self, i1, b, i2):
        self.field1 = i1
        self.field_boolean = b
        self.field2 = i2


class SchemaTableModelCheckStateTest(unittest.TestCase):
    """Ensure that the SchemaTableModel works properly with fields.Boolean
    and Qt.CheckStateRole.

    """
    def setUp(self):
        data = [ThingWithBoolean(0, True, 0),
                ThingWithBoolean(1, True, 0),
                ThingWithBoolean(0, False, 42)]
        self.model = SchemaTableModel(SchemaWithBoolean, ThingWithBoolean,
                                      data=data)

    def test_data(self):
        index = self.model.index(0, 1)
        self.assertEqual(self.model.data(index), True)
        # This one is a bit weird, but needed because for whatever
        # stupid reason QCheckbox-s treat 1 as "intermediate state"
        self.assertEqual(self.model.data(index, role=Qt.CheckStateRole), 2)

        index = self.model.index(2, 2)
        self.assertEqual(self.model.data(index), 42)
        self.assertEqual(self.model.data(index, role=Qt.CheckStateRole),
                         QVariant())

    def test_setData(self):
        index = self.model.index(0, 1)
        self.assertTrue(self.model.setData(index, False))
        self.assertTrue(self.model.setData(index, False, Qt.CheckStateRole))

        index = self.model.index(2, 2)
        self.assertTrue(self.model.setData(index, 0))
        self.assertFalse(self.model.setData(index, 42, role=Qt.CheckStateRole))


class SchemaWithDate(Schema):
    date = fields.Date()
    datetime = fields.DateTime()


class ThingWithDate:
    def __init__(self, d, dt):
        self.date = dtparse(d)
        self.datetime = dtparse(dt)


class TestSchemaTableModelDate:
    def test_data(self):
        """Ensure that the ``data()`` method of a SchemaTableModel correctly
        wraps objects corresponding to dates to a ``QDate`` or ``QDateTime``
        instance.

        """
        data = (("1991-01-01", "1995-06-06 19:53:10"),
                ("2013-12-12", "2017-12-12 19:54:22"))
        model_data = [ThingWithDate(*row) for row in data]
        model = SchemaTableModel(SchemaWithDate, ThingWithDate, data=model_data)
        # expected = ((QDate.fromString(date, Qt.ISODate),
        expected = ((QDateTime.fromString(date, Qt.ISODate),  # FIXME qdate
                     QDateTime.fromString(datetime, Qt.ISODate))
                    for date, datetime in data)

        for i, expected_row in enumerate(expected):
            for j, (cls, expected_cell) in enumerate(zip([QDate, QDateTime],
                                                         expected_row)):
                cell_data = model.data(model.index(i, j))
                # assert isinstance(cell_data, cls)
                assert isinstance(cell_data, QDateTime)  # FIXME support qdate
                assert cell_data == expected_cell


class TestReadOnlyListModel:
    def test_basic(self):
        data = ["foo", "bar", "baz"]
        model = ReadOnlyListModel(data)
        assert model.rowCount(QModelIndex()) == 3
        assert model.columnCount(QModelIndex()) == 1

    def test_item(self):
        data = ["foo", "bar", "baz"]
        model = ReadOnlyListModel(data)
        assert model.data(model.index(0, 0)) == "foo"
        assert model.data(model.index(1, 0)) == "bar"
        assert model.data(model.index(2, 0)) == "baz"

    def test_attr(self):
        data = ["foo", "bar", "baz"]

        class FooObject:
            def __init__(self, thing):
                self.thing = thing
        foodata = [FooObject(thing) for thing in data]
        model = ReadOnlyListModel(foodata, attr="thing")

        assert model.rowCount(QModelIndex()) == 3
        assert model.data(model.index(0, 0)) == "foo"
        assert model.data(model.index(1, 0)) == "bar"
        assert model.data(model.index(2, 0)) == "baz"

        with pytest.raises(AttributeError):
            ReadOnlyListModel(data, attr="this does not exist'")
