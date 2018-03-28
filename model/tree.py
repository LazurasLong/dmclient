# model/tree.py
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

"""
dmclient's "asset tree", the central tree-like structure exposing most of the
campaign elements up-front.

Classes of type ``TreeNode`` have:

1. An ID,
2. an (opaquely known) icon,
3. an action, and
4. a list of column delegates

These nodes form a tree whose root is passed into a ``TreeModel`` for use with
``QTreeView`` and the like.

Node types
----------

- ``TreeNode``. Common ABC of node types.

- ``FixedNode``. Built programmatically. Supports "just" strings as

- ``TableNode``. Points to a database table and displays a the list of
  objects in that table.

- ``AttrNode``. Receives a python object (which may be from the ORM) and an
  optional list of attribute names to display as children.

- ``ForeignAttrNode``. Like ``AttrNode``, but the column is assumed to contain
  a foreign key ID which is then cross-referenced in a different table. The
  resulting looked up object is assigned as an ``AttrNode``.

"Tables" are referenced by either an SQLAlchemy ``Table`` object, or by a
declarative schema class.

Node actions
------------

Nodes have an *action*, which the model coordinates dispatch of. The action
handler is always passed the id of the node.

Nodes also have an *alternate action*, which is typically used to implement
context menu handlers via passing in the handler routine as the alternate
action. ``TreeModel`` is then capable of retrieving these actions via
``DMRole.action_role`` and ``DMRole.altaction_role`` respectively.

Column delegates
----------------

Delegates may be assigned to a given column, which causes children to be
descended as a tree node of the delegates type. For example, combining a

For example, ``TableNode`` and ``AttrNode`` may be combined to form useful
displays of data: after assigning a delegate to database column ``i`` of the
``TableNode``, the object returned (ending up in as child row ``i`` of
the tree node) is displayed within an ``AttrNode``.

Module contents
---------------

"""

from logging import getLogger

from PyQt5.QtCore import QAbstractItemModel, QModelIndex, QVariant, Qt, pyqtSlot

from model.qt import DMRole
from model.schema import Schema

__all__ = ["TreeNode", "FixedNode", "TableNode", "TreeModel"]

log = getLogger(__name__)


class TreeNode:
    def __init__(self, action=None, item_action=None,
                 icon=None, text="", parent=None, id=None, delegate=None):
        self.action = action
        self.item_action = item_action
        self.icon = icon
        self.text = text
        self.parent = parent
        self.id = id
        self.delegate = delegate

    @property
    def children(self):
        raise NotImplementedError

    def __len__(self):
        return len(self.children)

    def __repr__(self):
        return ("{}({}, text=\"{}\", #children={})"
                .format(self.__class__.__name__,
                        self.icon,
                        self.text, len(self)))

    def update(self):
        for child in self.children:
            child.update()


class BadNode(TreeNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def children(self):
        return []


class FixedNode(TreeNode):
    def __init__(self, *children, **kwargs):
        super().__init__(**kwargs)
        self._children = children
        for child in children:
            child.parent = self

    @property
    def children(self):
        return self._children


class AttrNode(TreeNode):
    def __init__(self, obj, *attr_names, **kwargs):
        super().__init__(**kwargs)
        assert all(hasattr(obj, attr) for attr in attr_names)
        self.obj = obj
        self.attr_names = attr_names
        self._children = []
        self.update()

    def update(self):
        self._children = [BadNode(text=str(item), parent=self,
                                  delegate=self.delegate)
                          for item in [getattr(self.obj, attr)
                                       for attr in self.attr_names]]

    @property
    def children(self):
        return self._children


class TableNode(TreeNode):
    """
    A tree node class suitable for displaying a database table.
    """

    def __init__(self, db, schema: Schema, *cols, **kwargs):
        """

        :param db: Database session.
        :param schema: The schema/table to monitor.
        :param cols: List of column names to display. If nothing is passed,
                     then every column is considered.
        :param kwargs: Passed to :py:class:`TreeNode`.
        """
        super().__init__(**kwargs)
        self.db = db
        self.schema = schema
        self._children = []
        self.update()

    @property
    def children(self):
        return self._children

    def update(self):
        res = self.db.query(self.schema).all()
        self._children = [BadNode(text=str(item), parent=self, id=item.id,
                                  delegate=self.delegate)
                          for item in res]


class TreeModel(QAbstractItemModel):
    """
    This class presents an item view suitable for tree views
    based on a :py:class:`TreeNode` hierarchy.

    Stores a tuple inside of the `internalPointer` of each model index. This
    tuple is a ``(parent_node, child_row_i)``. If the index does not correspond
    to a leaf node, then ``child_row_i`` will be ``-1``.

    .. todo::
        This class is read-only; support some kind of editing!

    .. todo::
        Support multiple columns.

    """

    def __init__(self, root: TreeNode, title="", parent=None):
        super().__init__(parent)
        self.root = root
        self.title = title

    @pyqtSlot(QModelIndex)
    def actionTriggered(self, index):
        node = index.internalPointer()
        if node.action:
            node.action(self.data(index, role=DMRole.id_role))

    # noinspection PyMethodOverriding
    def columnCount(self, parent=QModelIndex()):
        return 1

    def data(self, index=QModelIndex(), role=Qt.DisplayRole):
        if not index.isValid() or role not in (Qt.DisplayRole,
                                               Qt.DecorationRole,
                                               DMRole.id_role):
            return QVariant()
        node = index.internalPointer()
        if role == Qt.DisplayRole:
            return node.text
        elif role == DMRole.id_role:
            return node.id
        elif role == Qt.DecorationRole:
            return node.icon
        assert False

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole or orientation == Qt.Vertical:
            return QVariant()
        return self.title

    # noinspection PyMethodOverriding
    def index(self, row, column, parent=QModelIndex()):
        if not parent.isValid():
            node = self.root
        else:
            node = parent.internalPointer()
        try:
            child = node.children[row]
        except IndexError:
            return QModelIndex()
        return self.createIndex(row, column, child)

    # noinspection PyMethodOverriding
    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        child_item = index.internalPointer()
        parent_item = child_item.parent
        if parent_item == self.root:
            return QModelIndex()
        row = parent_item.parent.children.index(parent_item)  # FIXME wtf.
        return self.createIndex(row, index.column(), parent_item)

    # noinspection PyMethodOverriding
    def rowCount(self, parent=QModelIndex()):
        if 0 < parent.column():
            return 0
        if not parent.isValid():
            parent = self.root
        else:
            parent = parent.internalPointer()
        return len(parent)
