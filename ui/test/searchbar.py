from collections import namedtuple

from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QStandardItem
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QVBoxLayout

from core.config import APP_NAME
# from ui import spacer_widget
from ui.search import SearchResultsWidget


class FakeOracle:
    """Some kind of dumbass oracle."""
    def __init__(self):
        self.search_sections = [
            "bleh"
        ]


SearchResult = namedtuple("SearchResult", ["name", "icon"])


class SearchResults:
    def __init__(self, original_query, results):
        self.original_query = original_query
        self.model = self._build_results_model(results)

    @classmethod
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


def build_results(query):
    icon = QIcon(":/icons/map.png")
    results = {
        "FooSection": [
            SearchResult("foofoo", icon),
            SearchResult("foobar", icon),
            SearchResult("foobaz", icon),
        ],
        "BarSection": [
            SearchResult("barfoo", icon),
            SearchResult("barbar", icon),
        ],
    }
    return results


def test_results_pane(window):
    dialog = QDialog(window)
    query = ""
    search_results = SearchResults(query, build_results(query))
    widget = SearchResultsWidget(dialog)
    widget.on_search_results(search_results.model)
    layout = QVBoxLayout()
    layout.addWidget(widget)
    dialog.setLayout(layout)
    return dialog


def guitest_main(main_window):
    main_window.setWindowTitle(APP_NAME)
    toolbar = main_window.addToolBar("Toolbar")
    toolbar.addAction(QAction(QIcon(":/icons/edit.png"), "Derp", toolbar))
    toolbar.addAction(QAction(QIcon(":/icons/castle.png"), "CASTLE!", toolbar))
    # toolbar.addWidget(spacer_widget())
    toolbar.addWidget(QLineEdit())
    main_window.resize(800, 600)

    test_dialog = test_results_pane(main_window)
    test_dialog.raise_()
    test_dialog.show()
