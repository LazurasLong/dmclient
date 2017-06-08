from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import *


__all__ = ["SearchResultsListView", "SearchResultsWidget"]


class TreeViewDelegate(QStyledItemDelegate):
    """Causes the headers to be painted prettily."""
    def paint(self, painter, option, index):
        # Not a section? Not relevant.
        if index.parent().isValid():
            return super().paint(painter, option, index)

        header_option = QStyleOptionHeader()
        header_option.position = QStyleOptionHeader.Middle
        QApplication.style().drawControl(QStyle.CE_HeaderLabel,
                                         header_option,
                                         painter)


class SearchResultsListView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIconSize(QSize(48, 48))
        self.setUniformRowHeights(True)
        self.setItemsExpandable(False)
        self.setIndentation(0)
        self.setHeaderHidden(True)
        # self.setItemDelegate(ThingDelegate(self))

    def setModel(self, model):
        super().setModel(model)
        self.expandAll()


class SearchResultsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.results_view = SearchResultsListView()
        self.layout.addWidget(self.results_view)

    def on_search_results(self, search_results):  # FIXME terrible name
        self.results_view.setModel(search_results)
