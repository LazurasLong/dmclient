# model/test/test_tree.py
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

"""Test the declarative dumb model tree crap that we've hastily thrown together.

"""

import pytest
from PyQt5.QtCore import QModelIndex, QVariant, Qt

from model.tree import AttrNode, DictNode, ListNode, Node, TreeModel


class FooClass:
    def __init__(self):
        self.i = 1
        self.s = "str"
        self.l = ["foo", 42]

    def __str__(self):
        return self.s


@pytest.fixture
def fooinst():
    """Instance of some model object."""
    return FooClass()


@pytest.fixture
def node():
    return Node()


class TestNode:
    def test_default_ctor(self, node):
        assert node.text == ""
        assert len(node.children) == 0
        assert node.parent is None

    def test_node_children(self, node):
        node.add_child(Node(text="foo"))
        assert len(node.children) == 1

    @pytest.mark.parametrize('o', (None, "foo", 42, {"foo": "bar"}))
    def test_apply(self, o):
        """Ensure that the ``Node.apply()`` function does not modify the node
        itself.

        """
        # Weird verification of duck typing expectations...
        node = Node(action="foo", icon="bar", text="baz")
        node.apply(o)
        assert node.action == "foo"
        assert node.icon == "bar"
        assert node.text == "baz"


class TestAttrNode:
    def test_default_ctor(self, fooinst):
        node = AttrNode("l")
        assert node.text == "L"
        assert len(node.children) == 0
        assert node.parent is None

    def test_attrnode_children_length(self, fooinst):
        node = AttrNode("l")
        node.apply(fooinst)
        assert len(node.children) == 2
        assert node.parent is None

    def test_str_as_leaf(self, fooinst):
        node = AttrNode("s")
        node.apply(fooinst)
        # FIXME: instances of str taking the property name implicitly?
        assert node.text == "str"
        assert len(node.children) == 0
        assert node.parent is None


class TestListNode:
    def test_basic(self):
        node = ListNode()
        node.apply("abc")  # Abuse of ducktyping!

        assert len(node.children) == 3


class TestNestedNodeTrees:
    def test_parent(self):
        root = Node()
        child = Node()
        root.add_child(child)
        assert root.parent is None
        assert child.parent is root

    def test_nodes(self):
        root = Node(
            Node(),
            Node(Node()),
            Node(Node(), Node()),
        )
        assert len(root.children[0]) == 0
        assert len(root.children[1]) == 1
        assert len(root.children[2]) == 2


class TestMixedNodeTrees:
    def test_node_children(self, fooinst):
        n = Node(text="foo")
        n.add_child(Node(text="bar"))
        root = Node(
            n,
            AttrNode("s")
        )
        root.apply(fooinst)

        assert len(root.children) == 2
        assert len(root.children[0]) == 1
        assert len(root.children[1]) == 0

        assert root.children[0].text == "foo"
        assert root.children[1].text == "str"
        assert root.children[0].children[0].text == "bar"


@pytest.fixture
def foodict(fooinst):
    return {i: fooinst for i in range(3)}


@pytest.fixture
def foodictfactory():
    factory = DictNodeFactory()
    factory


class TestDictNodes:
    def test_basic(self, foodict):
        node = DictNode()
        node.apply(foodict)
        assert len(node) == len(foodict)


def _walk_to(model, *children):
    """Given a list of children from the root, return
    the index for that given

    """
    index = QModelIndex()
    for i, child_i in enumerate(children):
        index = model.index(child_i, 0, index)
        assert index.isValid(), "children[{}] = {}".format(i, child_i)
    return index


@pytest.fixture(scope="module")
def big_node_tree():
    return Node(Node(Node(text="foo"), Node(text="bar"), Node(text="baz")),
                Node(text="spam"), Node(text="eggs"),
                Node(Node(text="a"), Node(text="b"), Node(text="c")),
                Node(Node(Node(Node()))))


@pytest.fixture(scope="module")
def tree_model(big_node_tree):
    return TreeModel(big_node_tree)


class TestBasicTreeModel:
    def test_title_header_data(self):
        model = TreeModel(Node(), title="FooHeader")
        assert model.headerData(0, Qt.Horizontal) == "FooHeader"
        assert model.headerData(0, Qt.Vertical) == QVariant()

    def test_flags(self):
        model = TreeModel(Node())
        assert model.flags(QModelIndex()) == (
            Qt.ItemIsEnabled | Qt.ItemIsSelectable)


class TestNodeTreeModel:
    def test_root(self, tree_model):
        assert tree_model.columnCount() == 1
        assert tree_model.rowCount() == 5

    @pytest.mark.parametrize('child_i,expected',
                             enumerate(["", "spam", "eggs", ""]))
    def test_first_level_data(self, tree_model, child_i, expected):
        index = _walk_to(tree_model, child_i)
        assert tree_model.data(index) == expected
        assert tree_model.data(index, Qt.DecorationRole) == QVariant()

    @pytest.mark.parametrize('child_i,expected', enumerate([3, 0, 0, 3, 1]))
    def test_first_level_rowcount(self, tree_model, child_i, expected):
        index = _walk_to(tree_model, child_i)
        assert tree_model.rowCount(
                index) == expected, "Expected rowCount {} for child `{}'".format(
                expected, child_i)

    def test_second_level(self, tree_model):
        index = _walk_to(tree_model, 0, 0)
        assert tree_model.rowCount(index) == 0, tree_model.data(index)
        assert tree_model.data(index) == "foo"

    def test_parent_root(self, tree_model):
        for i in range(tree_model.rowCount(QModelIndex())):
            assert _walk_to(tree_model, i).parent() == QModelIndex()

    def test_parent_nonroot(self, tree_model):
        assert _walk_to(tree_model, 0, 0).parent() == _walk_to(tree_model, 0)
        assert _walk_to(tree_model, 0, 1).parent() == _walk_to(tree_model, 0)


class FooClass:  # FIXME duplicated in model/test/test_tree.py
    def __init__(self):
        self.i = 1
        self.s = "str"
        self.l = ["foo", 42]

    def __str__(self):
        return self.s


class FooContainer:
    attr1 = "eggs"
    attr2 = [FooClass()] * 2


@pytest.fixture
def attr_tree():
    foo = FooContainer()
    c1 = AttrNode("attr1")
    c2 = AttrNode("attr2")
    root = Node(c1, c2)
    root.apply(foo)
    return root


@pytest.fixture
def attr_model(attr_tree):
    return TreeModel(attr_tree)


class TestAttrNodeTreeModel:
    def test_basic_attrnode(self, attr_model):
        index = _walk_to(attr_model, 0)
        assert attr_model.data(index) == "eggs"

    def test_list_attrnode(self, attr_model):
        index = _walk_to(attr_model, 1)
        assert attr_model.rowCount(index) == 2

    def test_nested_attrnode(self, attr_model):
        index = _walk_to(attr_model, 1, 0)
        assert attr_model.data(
                index) == "str", "the AttrNode children should be Nodes implicitly using __str__"


class TestMixedNodeTreeModel:
    def test_thing(self):
        class FooCampaign:
            regional_maps = ["r0", "r1", "r2"]
            encounter_maps = ["e0", "e1", "e2", "e3"]
            sessions = [1, 2, 3, 4, 5]

        map_node = Node(AttrNode("regional_maps", text="Regional"),
                        AttrNode("encounter_maps", text="Encounters"),
                        text="Maps")
        session_node = AttrNode("sessions")

        root = Node()
        root.add_child(map_node)
        root.add_child(session_node)
        root.apply(FooCampaign)

        model = TreeModel(root)

        assert model.rowCount(QModelIndex()) == 2
        assert model.rowCount(_walk_to(model, 0)) == 2
        assert model.rowCount(_walk_to(model, 1)) == 5

        assert _walk_to(model, 0, 1).parent() == _walk_to(model, 0)

        for attr_i, attr in enumerate(
                [FooCampaign.regional_maps, FooCampaign.encounter_maps]):
            parent_index = _walk_to(model, 0, attr_i)
            for child_i, val in enumerate(attr):
                index = _walk_to(model, 0, attr_i, child_i)
                assert model.data(index) == val
                assert index.parent() == parent_index

        parent_index = _walk_to(model, 1)  # sessions
        for child_i, val in enumerate(FooCampaign.sessions):
            index = _walk_to(model, 1, child_i)
            assert model.data(index) == str(val)
            assert index.parent() == parent_index
