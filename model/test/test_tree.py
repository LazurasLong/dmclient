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

import pytest
from PyQt5.QtCore import QModelIndex, QVariant, Qt
from sqlalchemy import Integer, String, Column, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from model.tree import AttrNode, TreeModel, FixedNode, TableNode


class TestFixedNode:
    def test_default_ctor(self):
        node = FixedNode()
        assert node.text == ""
        assert len(node.children) == 0
        assert node.parent is None

    def test_ctor(self):
        node = FixedNode(text="Foo")
        assert node.text == "Foo"
        assert len(node.children) == 0
        assert node.parent is None

    def test_node_children(self):
        node = FixedNode(FixedNode())
        assert len(node.children) == 1

    def test_parent(self):
        child = FixedNode()
        root = FixedNode(child)
        assert root.parent is None
        assert child.parent is root

    def test_multiple_levels(self):
        root = FixedNode(
            FixedNode(),
            FixedNode(FixedNode()),
            FixedNode(FixedNode(), FixedNode()),
        )
        assert len(root.children[0]) == 0
        assert len(root.children[1]) == 1
        assert len(root.children[2]) == 2


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


class TestAttrNode:
    def test_one_child(self, fooinst):
        node = AttrNode(fooinst, "l", text="Node")
        assert node.text == "Node"
        assert len(node.children) == 1
        assert node.parent is None
        child = node.children[0]
        assert child.parent is node
        assert child.text == repr(fooinst.l)  # uhh

    def test_multiple_attributes(self, fooinst):
        node = AttrNode(fooinst, "i", "l")
        assert node.text == ""
        assert len(node.children) == 2
        assert node.parent is None
        assert node.children[0].text == '1'
        assert node.children[1].text == repr(fooinst.l)  # uhh


Base = declarative_base()


class FooTableClass(Base):
    __tablename__ = "foo"

    id = Column(Integer, primary_key=True)
    thing1 = Column(Integer, default=42)
    thing2 = Column(String, default="foo")

    def __str__(self):
        return self.thing2


@pytest.fixture(scope="module")
def mock_db():
    engine = create_engine("sqlite:///:memory:")
    session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return engine, session()


@pytest.fixture(scope="module")
def foodb(mock_db):
    _, session = mock_db
    session.add(FooTableClass())
    session.add(FooTableClass(thing1=999, thing2="bar"))
    session.add(FooTableClass(thing1=0, thing2=""))
    return session


class TestTableNode:
    @pytest.fixture(scope="class")
    def tablenode(self, foodb):
        node = TableNode(foodb, FooTableClass)

        return node

    def test_children(self, tablenode):
        assert len(tablenode.children) == 3


def _walk_to(model, *children):
    """
    Given a list of children arguments specified relative from the root, return
    the corresponding tail of ``QModelIndex`` instance.

    For example, given a balanced ternary tree of height 3 and a path
    ``[0, 1, 2, 1]`` returns the index for the leaf node if one traverses the
    0th (left-most) child, 1st (middle) child, 2nd (right-most), and 1st (leaf)
    child.
    """
    index = QModelIndex()
    for i, child_i in enumerate(children):
        index = model.index(child_i, 0, index)
        assert index.isValid(), "children[{}] = {}".format(i, child_i)
    return index


@pytest.fixture(scope="module")
def big_fixed_node_tree():
    tree = FixedNode(
        FixedNode(
            FixedNode(text="foo"),
            FixedNode(text="bar"),
            FixedNode(text="baz")),
        FixedNode(text="spam"),
        FixedNode(text="eggs"),
        FixedNode(
            FixedNode(text="a"),
            FixedNode(text="b"),
            FixedNode(text="c")),
        FixedNode(FixedNode(FixedNode(FixedNode()))))
    return tree


@pytest.fixture(scope="module")
def tree_model(big_fixed_node_tree):
    return TreeModel(big_fixed_node_tree)


class TestTreeModelProperties:
    """
    Test some non-node related functionality.
    """
    def test_title_header_data(self):
        model = TreeModel(FixedNode(), title="FooHeader")
        assert model.headerData(0, Qt.Horizontal) == "FooHeader"
        assert model.headerData(0, Qt.Vertical) == QVariant()

    def test_flags(self):
        model = TreeModel(FixedNode())
        assert model.flags(QModelIndex()) == (
            Qt.ItemIsEnabled | Qt.ItemIsSelectable)


class TestFixedNodeTreeModel:
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
            supposed_root_index = _walk_to(tree_model, i).parent()
            assert QModelIndex() == supposed_root_index

    def test_parent_nonroot(self, tree_model):
        assert _walk_to(tree_model, 0, 0).parent() == _walk_to(tree_model, 0)
        assert _walk_to(tree_model, 0, 1).parent() == _walk_to(tree_model, 0)


class FooContainer:
    attr1 = "eggs"
    attr2 = [FooClass()] * 2


@pytest.fixture
def attr_tree():
    return AttrNode(FooContainer, "attr1", "attr2")


@pytest.fixture
def attr_model(attr_tree):
    return TreeModel(attr_tree)


class TestAttrNodeTreeModel:
    def test_basic_attrnode(self, attr_model):
        index = _walk_to(attr_model, 0)
        assert attr_model.data(index) == "eggs"

    # TODO Test the contents of the list node?

    def test_list_attrnode(self, attr_model):
        index = _walk_to(attr_model, 1)
        assert attr_model.rowCount(index) == 0


class TestTableNodeTreeModel:
    @pytest.fixture(scope="class")
    def foomodel(self, foodb):
        root = TableNode(foodb, FooTableClass, text="Foo")
        model = TreeModel(root)
        return model

    def test_row_count(self, foomodel):
        assert 3 == foomodel.rowCount(QModelIndex())

    @pytest.mark.parametrize('child_i,expected', enumerate(["foo", "bar", ""]))
    def test_displayrole(self, foomodel, child_i, expected):
        index = foomodel.index(child_i, 0, QModelIndex())
        assert expected == foomodel.data(index)
