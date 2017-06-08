from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import QWidget

from ui.actions import ActionManager, tool


def create_colour_icon(name):
    pixmap = QPixmap(64, 64)
    painter = QPainter(pixmap)
    painter.fillRect(QRectF(0.0, 0.0, 64.0, 64.0), QColor(name))
    painter.end()
    icon = QIcon(pixmap)
    return icon


class SomeActionManagerGuy(ActionManager):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def set_colour(self, colour):
        self.widget.setStyleSheet("background-color: {};".format(colour))

    @tool
    def orange(self):
        self.set_colour("orange")

    @tool(name="This is gonna be set to blue!")
    def blue(self):
        self.set_colour("blue")

    # This guy has no icon nor text; test zero argument version of @tool
    @tool
    def green(self):
        self.set_colour("green")


def guitest_main(main_window):
    widget = QWidget(main_window)
    main_window.setCentralWidget(widget)
    main_window.resize(640, 480)
    manager = SomeActionManagerGuy(widget)
    main_window.addToolBar(manager.toolbar(main_window))
