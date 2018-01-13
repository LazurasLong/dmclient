# test/schemamap.py
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

import sys
import unittest

from PyQt5.QtCore import QDate, QDateTime
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import *
from marshmallow import fields

from model.schema import Schema
from ui.schemamap import schema_ui_map

qapp = QApplication(sys.argv)


class StringSchema(Schema):
    """A schema with nothing but strings."""
    field1 = fields.Str()
    field2 = fields.Str()


class BasicStringSchemaTest(unittest.TestCase):
    def setUp(self):
        self.model = QStandardItemModel()
        self.model.insertColumn(0, [QStandardItem("foo")])
        self.model.insertColumn(1, [QStandardItem("bar")])
        self.parent_widget = QWidget()

    def test_mapper(self):
        edit1 = QLineEdit(self.parent_widget)
        edit1.setObjectName("field1")
        edit2 = QLineEdit(self.parent_widget)
        edit2.setObjectName("field2")

        mapper = schema_ui_map(StringSchema, self.model, self.parent_widget)

        self.assertEqual(edit1.text(), "foo")
        self.assertEqual(edit2.text(), "bar")

    def test_mapper_labels(self):
        """Test out the schemamap with QLabels."""
        label1 = QLabel(self.parent_widget)
        label1.setObjectName("field1")
        label2 = QLabel(self.parent_widget)
        label2.setObjectName("field2")

        mapper = schema_ui_map(StringSchema, self.model, self.parent_widget)

        self.assertEqual(label1.text(), "foo")
        self.assertEqual(label2.text(), "bar")

    def test_plaintextedit(self):
        edit1 = QPlainTextEdit(self.parent_widget)
        edit1.setObjectName("field1")

        mapper = schema_ui_map(StringSchema, self.model, self.parent_widget)

        self.assertEqual(edit1.toPlainText(), "foo")


class VarietySchema(Schema):
    """Test out a variety of field types."""
    field_int = fields.Integer()
    field_float = fields.Float()
    field_boolean = fields.Boolean()
    field_date = fields.DateTime()


class TestVarieties(unittest.TestCase):
    def setUp(self):
        self.model = QStandardItemModel()
        self.parent_widget = QWidget()

    def test_ints(self):
        item = QStandardItem("42")
        self.model.appendRow(item)

        spinner = QSpinBox(self.parent_widget)
        spinner.setObjectName("field_int")

        mapper = schema_ui_map(VarietySchema, self.model, self.parent_widget)

        self.assertEqual(spinner.value(), 42)

    def test_boolean(self):
        self.model.setItem(0, 2, QStandardItem("true"))

        checkbox = QCheckBox(self.parent_widget)
        checkbox.setObjectName("field_boolean")

        mapper = schema_ui_map(VarietySchema, self.model, self.parent_widget)

        self.assertTrue(checkbox.isChecked())

    def test_date_label(self):
        datetime = QDateTime()
        datetime.setDate(QDate.currentDate())
        self.model.setItem(0, 3, QStandardItem(datetime.toString()))

        label = QLabel(self.parent_widget)
        label.setObjectName("field_date")

        mapper = schema_ui_map(VarietySchema, self.model, self.parent_widget)

        self.assertEqual(label.text(), datetime.toString())

    def test_mappedSection(self):
        spinner = QSpinBox(self.parent_widget)
        spinner.setObjectName("field_int")
        bad_checkbox = QCheckBox(self.parent_widget)
        bad_checkbox.setObjectName("field_DOES_NOT_EXIST")
        label = QLabel(self.parent_widget)
        label.setObjectName("field_date")

        mapper = schema_ui_map(VarietySchema, self.model, self.parent_widget)

        self.assertEqual(mapper.mappedSection(spinner), 0)
        self.assertEqual(mapper.mappedSection(label), 3)

        self.assertEqual(mapper.mappedSection(bad_checkbox), -1)

if __name__ == '__main__':
    unittest.main()
