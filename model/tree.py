# model/tree.py
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

"""Some kind of pythonic-ish tree structure exposing a object hierarchy. Poorly.

"""

from logging import getLogger

from PyQt5.QtCore import QAbstractItemModel, QModelIndex, QVariant, Qt, pyqtSlot, pyqtSignal

from core import hrname
from model.qt import DMRole

__all__ = ["Node", "ListNode", "DictNode", "NodeFactory"]

log = getLogger(__name__)


class Node:
    def __init__(self, action=None, icon=None, text="", parent=None, id=None,
                 delegate=None):
        self.action = action
        self.icon = icon
        self.text = text
        self.parent = parent
        self.id = id
        self.children = []
        self.delegate = delegate

    def __len__(self):
        return len(self.children)

    def __repr__(self):
        return "Node({}, text=\"{}\", #children={})".format(self.icon,
                                                            self.text,
                                                            len(self.children))

    def add_children(self, children):
        for child in children:
            self.add_child(child)

    def add_child(self, child):
        assert isinstance(child, Node)
        self.children.append(child)
        child.parent = self

    def apply(self, o):
        """Apply an object to this tree, establishing the mappings?!"""
        if not self.text:
            self.text = str(o)


class AttrNode(Node):
    def __init__(self, attr_name, child_cls=Node, action=None, icon=None,
                 text=""):
        """AttrNode specifies a formula for a later-applied object. It is
        essentially a wrapper for another type of node ``child_cls``.

        Keyword arguments:
        attr_name -- name of attr to look for
        child_cls -- Node class for the thing
        text -- text for the node name. If Falsey, ``hrname(attr_name)``

        """
        if not text:
            text = hrname(attr_name)
        super().__init__(action=action, icon=icon, text=text)
        self.attr_name = attr_name
        self.child_cls = child_cls

    def apply(self, o):
        child_cls = self.child_cls
        attr = getattr(o, self.attr_name)
        try:
            # Gross, this is a bit hacky.
            if isinstance(attr, str):
                raise TypeError

            for thing in attr:
                child = child_cls(text=str(thing))
                self.add_child(child)
        except TypeError:
            self.text = str(attr)


class ListNode(Node):
    def __init__(self, action=None, icon=None, text="", child_factory=None,
                 delegate=None):
        super().__init__(action, icon, text, delegate=delegate)
        if child_factory is None:
            child_factory = NodeFactory()
        self.child_factory = child_factory

    def apply(self, l):
        child_factory = self.child_factory
        for thing in l:
            node = child_factory.create(thing, self)
            self.children.append(node)


class DictNode(Node):
    """A tree node class for wrapping dictionaries. The values form the children
    of this node.

    .. note::
        This class assumes the ordered dict property of CPython 3.6.
    """

    def __init__(self, action=None, icon=None, text="", child_factory=None):
        super().__init__(action, icon, text)
        if child_factory is None:
            child_factory = NodeFactory()
        self.child_factory = child_factory
        self._dict = None
        self._dict_children = []
        self._child_wrapper = None

    def apply(self, d):
        factory = self.child_factory
        self.children = [factory.create(v, self, id=k) for k, v in d.items()]
        log.debug("{}".format(self.children))


class NodeFactory:
    """A ``NodeFactory`` allows a ``ListNode`` or ``DictNode`` to create
    customised nodes for their children entries.

    Parameters of this class are used in the created child objects.

    .. todo::
        Does it make sense to pass in the ``parent`` to ``.create()``? It allows
        the factories to be reused...
    """

    def __init__(self, action=None, icon=None):
        self.action = action
        self.icon = icon

    def create(self, o, parent, icon=None, text="", id=None):
        if not text:
            text = str(o)
        if not icon:
            icon = self.icon
        node = Node(self.action, icon, text, parent, id)
        return node


class TreeModel(QAbstractItemModel):
    """This class presents an item view suitable for tree views
    based on a :py:class:`model.tree.Node` hierarchy.

    This class is mostly based on the "Simple Tree Model" example.

    .. todo::
        This class is read-only; support some kind of editing!

    .. todo::
        Support multiple columns.

    """

    def __init__(self, root: Node, title="", parent=None):
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

    def data(self, parent=QModelIndex(), role=Qt.DisplayRole):
        if not parent.isValid() or role not in (Qt.DisplayRole,
                                                Qt.DecorationRole,
                                                DMRole.id_role):
            return QVariant()
        node = parent.internalPointer()
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
