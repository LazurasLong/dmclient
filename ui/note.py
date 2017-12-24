from PyQt5.QtCore import QSize, QTimer, QMetaObject, pyqtSlot
from PyQt5.QtWidgets import *


class NoteEditorDialog(QDialog):
    def __init__(self, note, db, parent=None):
        super().__init__(parent)
        self.note = note
        self.db = db

        self.timer = QTimer(self)
        self.timer.setObjectName("timer")
        self.timer.setInterval(4000)
        self.timer.setSingleShot(True)

        self.editor = QPlainTextEdit(self)
        self.editor.textChanged.connect(self.timer.start)
        self.editor.setPlainText(note.text)

        layout = QVBoxLayout()
        layout.addWidget(self.editor)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
                              self)
        layout.addWidget(bb)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)

        self.setLayout(layout)
        self.resize(QSize(480, 320))

        QMetaObject.connectSlotsByName(self)

    @pyqtSlot()
    def on_timer_timeout(self):
        self.note.text = self.editor.toPlainText()

    def accept(self):
        self.db.commit()
        super().accept()

    def reject(self):
        self.db.rollback()
        super().reject()
