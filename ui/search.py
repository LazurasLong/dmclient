# oracle/__init__.py
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

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import *

from widgets import ProgressIndicator


__all__ = ["SearchCompleter", "SearchQueryEdit", "SearchResultsView",
           "SearchResultsListView", "TreeViewDelegate"]


class SearchQueryEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCompleter(SearchCompleter())
        self.setPlaceholderText("Enter search query")
        self.setFocusPolicy(Qt.StrongFocus)


class SearchCompleter(QCompleter):
    def __init__(self):
        super().__init__()
        self.setCompletionMode(QCompleter.PopupCompletion)

    def showIndexingBlurb(self):
        pass

    def hideIndexingBlurb(self):
        pass


class SearchResultsView(QAbstractItemView):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.addSpacerItem(
                QSpacerItem(4, 4, QSizePolicy.Expanding, QSizePolicy.Minimum))

        indicator = ProgressIndicator()
        indicator.startAnimation()
        layout.addWidget(indicator)

        text = QLabel(self.grey_text("dmclient is indexing your documents..."))
        text.setTextFormat(Qt.RichText)
        layout.addWidget(text)

        layout.addSpacerItem(
                QSpacerItem(4, 4, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.indexing_blurb = QWidget(self)
        self.indexing_blurb.setLayout(layout)
        self.indexing_blurb.hide()

    @staticmethod
    def grey_text(text):
        return (
            "<html><head/><body><p><span style=\"font-size:12px;font-style:italic; color:#4a4a4a;\">{}</span></p></body></html>".format(
                    text))


class TreeViewDelegate(QStyledItemDelegate):
    """Causes the headers to be painted prettily."""

    def paint(self, painter, option, index):
        # Not a section? Not relevant.
        if index.parent().isValid():
            return super().paint(painter, option, index)

        header_option = QStyleOptionHeader()
        header_option.position = QStyleOptionHeader.Middle
        QApplication.style().drawControl(QStyle.CE_HeaderLabel, header_option,
                                         painter)


class SearchResultsListView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIconSize(QSize(48, 48))
        self.setUniformRowHeights(True)
        self.setItemsExpandable(False)
        self.setIndentation(0)
        self.setItemDelegate(TreeViewDelegate(self))
        self.setHeaderHidden(True)

    def setModel(self, model):
        super().setModel(model)
        self.expandAll()
