import os
from collections import namedtuple

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QDialogButtonBox

from campaign.controller import SearchViewController
from core.config import APP_NAME, CONFIG_PATH
from dmclient import init_logging
from oracle import DummyDelphi, spawn_oracle
from ui import spacer_widget
from ui.search import SearchQueryEdit

controller = None  # gross


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


class OracleArgs:
    disable_oracle = False
    logfile = os.path.join(CONFIG_PATH, "dmoracle.log")
    loggers = []


class ConsoleDialog(QDialog):
    def __init__(self):
        buttonBox = QDialogButtonBox()


def guitest_main(main_window):
    args = OracleArgs()
    init_logging(args)
    delphi = spawn_oracle(args)

    main_window.setWindowTitle(APP_NAME)
    main_window.resize(800, 600)

    edit = SearchQueryEdit()
    fake_oracle = DummyDelphi()
    global controller
    controller = SearchViewController(fake_oracle, edit.completer())
    edit.textChanged.connect(controller.on_search_text_changed)

    toolbar = main_window.addToolBar("Toolbar")
    action = QAction(QIcon(":/icons/edit.png"), "Derp", toolbar)
    toolbar.addAction(action)
    toolbar.addWidget(spacer_widget(main_window))
    toolbar.addWidget(edit)
