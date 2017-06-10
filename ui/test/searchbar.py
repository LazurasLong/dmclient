from collections import namedtuple

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QLineEdit, QMainWindow

from campaign.controller import SearchController
from core.config import APP_NAME
from ui.search import SearchResultsWidget


class FakeOracle:
    """Some kind of dumbass oracle."""

    def __init__(self):
        self.search_sections = [
            "bleh"
        ]


SearchResult = namedtuple("SearchResult", ["name", "icon"])


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


class MainWindow(QMainWindow):
    windowMoved = pyqtSignal()
    windowResized = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.move_cb = None
        self.resize_cb = None

    def moveEvent(self, event):
        self.windowMoved.emit()
        super().moveEvent(event)

    def resizeEvent(self, event):
        self.windowResized.emit()
        super().resizeEvent(event)


def guitest_main(main_window):
    main_window.setWindowTitle(APP_NAME)
    main_window.resize(800, 600)

    edit = QLineEdit()
    results_popup = SearchResultsWidget(main_window)
    controller = SearchController(None, edit, results_popup)
    main_window.windowMoved.connect(controller.update_results_popup)
    main_window.windowResized.connect(controller.update_results_popup)

    toolbar = main_window.addToolBar("Toolbar")
    action = QAction(QIcon(":/icons/edit.png"), "Derp", toolbar)
    toolbar.addAction(action)

    def f():
        controller.set_blurb_visible(True)

    action = QAction(QIcon(":/icons/castle.png"), "CASTLE!", toolbar)
    toolbar.addAction(action)

    def f():
        controller.results_visible = True

    action.triggered.connect(f)
    # toolbar.addWidget(spacer_widget())
    toolbar.addWidget(edit)
