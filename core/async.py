from PyQt5.QtCore import QTimer, pyqtSlot


def mtexec(f):
    """
    Wraps a function *f* so that execution occurs in the Qt main thread.
    """

    def _wrapper(*args, **kwargs):
        @pyqtSlot()
        def _wrapper2():
            f(*args, **kwargs)
        QTimer.singleShot(0, _wrapper2)

    return _wrapper
