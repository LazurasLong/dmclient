# model/qt.py
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

"""This module provides model adapters for native Python types and
dmclient-specific shenanigans """

from enum import Enum
from logging import getLogger

from PyQt5.QtCore import QAbstractListModel, QAbstractTableModel, QDate, \
    QDateTime, QModelIndex, QTime, QVariant, Qt
from marshmallow.fields import Boolean, Date, DateTime

__all__ = ["AbstractQtModel",
           "SchemaTableModel",
           "ListModel",
           "ReadOnlyListModel"]

log = getLogger(__name__)


class DMRole(Enum):
    id_role = Qt.UserRole


def qdatetime(datetime):
    """Turn a ``datetime.datetime`` object into a ``QDateTime``."""
    date = QDate(datetime.year, datetime.month, datetime.day)
    time = QTime(datetime.hour, datetime.minute, datetime.second)
    return QDateTime(date, time)


class ReadOnlyListModel(QAbstractListModel):
    """Takes in a Python list and presents it to Qt, but is otherwise unaware of
    what is stored within. Optionally takes in an `attr` parameter which is used
    for the `data()` method.

    """
    def __init__(self, data, parent=None, attr=None):
        super().__init__(parent)
        self._data = data
        # Remove one level of indirection.
        self._attr = attr
        if attr is None:
            self.data = self._itemdata
        else:
            getattr(data[0], attr)  # since hasattr() just does try..except ...
            self.data = self._attrdata

    def columnCount(self, *args, **kwargs):
        return 1

    # noinspection PyMethodOverriding
    def rowCount(self, index):
        return len(self._data)

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren

    # noinspection PyMethodOverriding
    def index(self, row, col, parent=None):
        return self.createIndex(row, col)

    def _itemdata(self, index, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        return self._data[index.row()]

    def _attrdata(self, index, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        item = self._data[index.row()]
        return getattr(item, self._attr)


class AbstractQtModel:
    """Common ancestor of adapter models for lists and schema tables.

    Stores an internal Python list and presents through a QAbstractItemModel
    interface. This class is abstract, however, and the ``columnCount()`` and
    ``data()`` methods do not have implementations.

    Instances of this class also (sort of) act like Python lists directly
    meaning you can conveniently call things like ``len()``.

    """
    def __init__(self, itemcls, items=None):
        """

        :param itemcls: default constructable item class
        :param items: some initial items (if you want)
        """
        if items is not None:
            assert isinstance(items, list), "no support for anything else yet"
        self.itemcls = itemcls
        self._data = items or []

    def __delitem__(self, key):
        del self._data[key]

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, key, value):
        self.beginInsertRows(QModelIndex(), key, 0)
        self._data.__setitem__(key, value)
        self.endInsertRows()

    def __str__(self):
        return str(self._data)

    def __len__(self):
        return len(self._data)

    def append(self, item):
        # FIXME this doesn't work with primitive types
        # if not isinstance(item, self.itemcls):
        #     raise TypeError("not a proper thing to add")
        self.beginInsertRows(QModelIndex(), len(self._data), len(self._data))
        self._data.append(item)
        self.endInsertRows()

    def index_(self, x, *args):
        """Pythonic ``index()`` method (but that symbol is taken by Qt so we add
        an underscore.)

        """
        return self._data.index(x, *args)

    def remove(self, x):
        row = self._data.index(x)
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._data[row]
        self.endRemoveRows()

    def insertRow(self, row, parent=QModelIndex()):
        self.beginInsertRows(parent, row, row)
        self._data.insert(row, self.itemcls())
        self.endInsertRows()

    def insertRows(self, row, count, parent=QModelIndex()):
        """Default constructs ``count`` objects of class ``itemcls`` and then
        stores them internally.

        """
        self.beginInsertRows(parent, row, row + count - 1)
        items = [self.itemcls() for _ in range(count)]
        self._data = self._data[:row] + items + self._data[row:]
        self.endInsertRows()
        return True

    def flags(self, index):
        if index.isValid():
            return 0
        return Qt.ItemIsEnabled

    def removeRow(self, row, parent=QModelIndex()):
        self.beginRemoveRows(parent, row, row)
        del self._data[row]
        self.endRemoveRows()
        return True

    def removeRows(self, start, end, parent=QModelIndex()):
        self.beginRemoveRows(parent, start, end)
        del self._data[start:end]
        self.endRemoveRows()
        return True

    def rowCount(self, parent=QModelIndex()):
        return len(self)


class ListModel(AbstractQtModel, QAbstractListModel):
    """Flexible list model adapter for Python lists to Qt list models.

    Stores an internal Python list and presents it via the QAbstractListModel
    interface. By default the ``data()`` method returns objects from the list
    passed through ``str()``.

    Instances of this class also (sort of) act like Python lists directly
    meaning you can conveniently call things like ``len()``.

    """

    def __init__(self, itemcls, data, parent=None):
        QAbstractListModel.__init__(self, parent)
        AbstractQtModel.__init__(self, itemcls, data)

    def columnCount(self, parent_index=QModelIndex()):
        return 1

    def data(self, parent_index, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        return self[parent_index.row()]

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemNeverHasChildren


class SchemaTableModel(AbstractQtModel, QAbstractTableModel):
    """This class is a simple model storing a list of items in a table according
     to their schema property.

    The rows are the individual domain objects and the columns map to
    properties as defined in the schema. For example, the following schema
    definition::

        class FooSchema(Schema):
            a = fields.Str()
            b = fields.Int()

    produces a model with two columns, one for ``a`` and one for ``b``. If one
    were to subclass ``FooSchema`` then its fields would be placed after the
    superclass::

        class BarSchema(FooSchema):
            c = fields.Str()

    produces a model with three columns: ``a``, ``b``, and then ``c``.

    By default the header names are taken from the field identifier names. It is
    up to views to prettify the headers beyond that using ``setHeaderData``.

    """

    def __init__(self, schema, itemcls, parent=None, data=None, readonly=False):
        """

        .. todo::
           Use one of cls or schema but don't require both.

        :param itemcls: domain model object class
        :param schema: The Schema for ``cls`` (helps determine columns)
        :param data: initial data to populate the model with
        :param parent: passed to QAbstractTableModel constructor
        """
        QAbstractTableModel.__init__(self, parent)
        AbstractQtModel.__init__(self, itemcls, data)

        self.itemcls = itemcls
        # TODO: can we avoid instantiating the schema?
        self.schema = schema
        s = schema()
        self._column_typemap = {  # FIXME remove this trash.
            Qt.CheckStateRole: tuple(i for i, field in enumerate(s.fields.values())
                                     if isinstance(field, Boolean)),
            "is_date_cls": tuple(i for i, field in enumerate(s.fields.values())
                                 if isinstance(field, (Date, DateTime))),
        }
        # Bleh, have to duplicate in-case setHeaderData
        # Read-only models will be more inteliberligernt about it.
        self._attr_names = list(s.fields.keys())
        self._header = list(s.fields.keys())
        self._header_decorations = [QVariant()] * len(self._header)
        self.readonly = readonly

    def __repr__(self):
        return "<SchemaTableModel(schema={}, " \
               "size=({},{}))>".format(self.schema,
                                       len(self),
                                       len(self._header))
    __str__ = __repr__

    # noinspection PyMethodOverriding
    def columnCount(self, parent):
        return len(self._header)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Vertical or role not in (Qt.DisplayRole, Qt.DecorationRole):
            return QVariant()
        if role == Qt.DisplayRole:
            return self._header[section]
        elif role == Qt.DecorationRole:
            return self._header_decorations[section]

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        if role not in (Qt.DisplayRole, Qt.EditRole, Qt.DecorationRole):
            raise NotImplementedError("I don't know what to do with {}".format(role))
        if orientation == Qt.Vertical or self.readonly:
            return False
        try:
            if role in (Qt.DisplayRole, Qt.EditRole):
                self._header[section] = value
            elif role == Qt.DecorationRole:
                self._header_decorations[section] = value
            self.headerDataChanged.emit(orientation, section, section)
            return True
        except IndexError as e:
            log.exception(e)
            return False

    def data(self, index, role=Qt.DisplayRole):
        # FIXME: this method is trash.
        if not index.isValid():
            return QVariant()
        if len(self) <= index.row() or len(self._header) <= index.column():
            return QVariant()  # TODO probably internal error so IndexError?
        if role not in (Qt.DisplayRole, Qt.EditRole, Qt.CheckStateRole):
            return QVariant()
        if role == Qt.CheckStateRole and index.column() not in self._column_typemap[Qt.CheckStateRole]:
                return QVariant()

        data = getattr(self._data[index.row()],
                       self._attr_names[index.column()])

        # Post-wrapping of type to Qt types (if necessary)
        if role == Qt.CheckStateRole:
            return 2 if data else 0
        elif role == Qt.DisplayRole and index.column() in self._column_typemap["is_date_cls"]:
            return qdatetime(data)

        return data

    def setData(self, index, value, role=Qt.EditRole):
        if self.readonly:
            return False
        _value = value
        if not index.isValid():
            log.error("index is not valid")
            return False
        if len(self._header) < index.column():
            log.error("requested setData on invalid column")
            return False
        if role not in (Qt.DisplayRole, Qt.EditRole, Qt.CheckStateRole):
            raise NotImplementedError("No idea what to do "
                                      "with that role `{}'.".format(role))
        if role == Qt.CheckStateRole:
            if not index.column() in self._column_typemap[Qt.CheckStateRole]:
                log.error("requested to setData on checkstate on non-boolean")
                return False
            _value = True if value == 2 else False

        attr = self._attr_names[index.column()]
        row = index.row() if index.row() != -1 else 0

        try:
            setattr(self._data[row], attr, _value)
        except IndexError:
            log.error("requested setData on non-existent row")
            return False

        self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if not self.readonly:
            flags |= Qt.ItemIsEditable
        if index.column() in self._column_typemap[Qt.CheckStateRole]:
            flags |= Qt.ItemIsUserCheckable
        return flags
