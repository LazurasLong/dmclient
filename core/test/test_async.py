import pytest
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication

from core.async import mtexec


@pytest.fixture(scope="module")
def qapp():
    return QApplication([])


class MockThread(QThread):
    def __init__(self, runnable):
        super().__init__()
        self.runnable = runnable

    def run(self):
        self.runnable()


class TestMtexec:
    def test_identity(self, qapp):
        def f():
            assert QApplication.instance().thread() == QThread.currentThread()

        f_mt = mtexec(f)
        f_mt()

    def test_different_thread(self):
        # TODO: If mtexec is taken away, this test doesn't fail, it just
        # SIGABRTs. Does that mean that, given that it passes and doesn't
        # SIGABRT, is the behaviour correct?!?!

        def f():
            assert QApplication.instance().thread() == QThread.currentThread()

        thread = MockThread(mtexec(f))
        thread.start()
        thread.wait(100)
