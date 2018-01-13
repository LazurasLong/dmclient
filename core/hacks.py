# core/hacks.py
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

"""This module provides dirty hacks to make PyQt more pleasant to work with.

.. todo::
    These should only be around when ``__debug__`` is turned on

"""

from PyQt5.QtCore import QDate
from PyQt5.QtCore import QDateTime
from PyQt5.QtCore import QItemSelection
from PyQt5.QtCore import QModelIndex

# If set to true, things like QModelIndexes will show their parent
# methods such as __repr__
from PyQt5.QtCore import QPointF

show_recursive_relationships = __debug__  # FIXME Should enable via cmdopt


def _qdate__repr__(qdate):
    return "<QDate({}-{}-{})>".format(qdate.year(), qdate.month(), qdate.day())


def _qdatetime__repr__(qdatetime):
    date, time = qdatetime.date(), qdatetime.time()
    return "<QDateTime({}-{}-{} {}:{}:{})>".format(date.year(),
                                                   date.month(),
                                                   date.day(),
                                                   time.hour(),
                                                   time.minute(),
                                                   time.second())


def _qitemselection__repr__(qitemselection):
    indexes = qitemselection.indexes()
    return "<QItemSelection({},{})>".format(len(indexes), indexes)


def _qmodelindex__repr__(index):
    if index.isValid():
        parent = index.parent()
        if show_recursive_relationships:
            parent_str = "{}".format(parent)
        else:
            parent_str = "{}".format(type(parent))
        return "<QModelIndex({}, {}, parent={}, model={})>".format(index.row(),
                                                                   index.column(),
                                                                   parent_str,
                                                                   index.model())
    else:
        return "<QModelIndex(<invalid>, model={})>".format(index.model())


def _qpointf__repr__(qpointf):
    return "QPointF({}, {})".format(qpointf.x(), qpointf.y())


def install_qt_reprs():
    QDate.__repr__ = _qdate__repr__
    QDateTime.__repr__ = _qdatetime__repr__
    QItemSelection.__repr__ = _qitemselection__repr__
    QModelIndex.__repr__ = _qmodelindex__repr__
    QPointF.__repr__ = _qpointf__repr__


def install_hacks():
    install_qt_reprs()
