from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import *

from widgets import ProgressIndicator

__all__ = ["SearchQueryEdit", "SearchResultsWidget"]


class SearchQueryEdit(QLineEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.setPlaceholderText("Enter search query...")


class SearchResultsWidget(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.FramelessWindowHint)
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.results_view = SearchResultsListView()
        self.layout.addWidget(self.results_view)

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
        self.layout.addWidget(self.indexing_blurb)

    def _build_results_model(cls, results):
        model = QStandardItemModel()
        for section in results:
            section_item = QStandardItem(section)
            section_item.setEditable(False)
            section_item.setSelectable(False)
            for name, icon in results[section]:
                item = QStandardItem(name)
                item.setIcon(icon)
                item.setEditable(False)
                section_item.appendRow(item)
            model.appendRow(section_item)
        return model

    @staticmethod
    def grey_text(text):
        return (
            "<html><head/><body><p><span style=\"font-size:12px;font-style:italic; color:#4a4a4a;\">{}</span></p></body></html>".format(
                    text))

    def on_search_results(self, search_results):  # FIXME terrible name
        self.results_view.setModel(search_results)


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
