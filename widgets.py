from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QSizePolicy, QWidget


class ProgressIndicator(QWidget):
    angle = None
    timerId = None
    delay = None
    displayedWhenStopped = None
    color = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timerId = -1
        self.delay = 70
        self.displayedWhenStopped = False
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFocusPolicy(Qt.NoFocus)
        self.show()

    def animationDelay(self):
        return self.delay

    def isAnimated(self):
        return (self.timerId != -1)

    def isDisplayedWhenStopped(self):
        return self.displayedWhenStopped

    def sizeHint(self):
        return QSize(20, 20)

    def startAnimation(self):
        self.angle = 0

        if self.timerId == -1:
            self.timerId = self.startTimer(self.delay)

    def stopAnimation(self):
        if self.timerId != -1:
            self.killTimer(self.timerId)

        self.timerId = -1
        self.update()

    def setDisplayedWhenStopped(self, state):
        self.displayedWhenStopped = state
        self.update()

    def timerEvent(self, event):
        self.angle = (self.angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        if not self.displayedWhenStopped and not self.isAnimated():
            return

        width = min(self.width(), self.height())

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        outerRadius = (width - 1) * 0.5
        innerRadius = (width - 1) * 0.5 * 0.38

        capsuleHeight = outerRadius - innerRadius
        capsuleWidth = capsuleHeight * .23 if (
            width > 32) else capsuleHeight * .35
        capsuleRadius = capsuleWidth / 2

        for i in range(0, 12):
            color = QColor(Qt.black)

            if self.isAnimated():
                color.setAlphaF(1.0 - (i / 12.0))
            else:
                color.setAlphaF(0.2)

            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.save()
            painter.translate(self.rect().center())
            painter.rotate(self.angle - (i * 30.0))
            painter.drawRoundedRect(capsuleWidth * -0.5,
                                    (innerRadius + capsuleHeight) * -1,
                                    capsuleWidth, capsuleHeight, capsuleRadius,
                                    capsuleRadius)
            painter.restore()
