# core/async.py
# Copyright (C) 2018 Alex Mair. All rights reserved.
# This file is part of dmclient.
#
# dmclient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# dmclient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with dmclient.  If not, see <http://www.gnu.org/licenses/>.
#

from PyQt5.QtCore import QTimer, pyqtSlot, QRunnable


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


class ProgressRunnable(QRunnable):
    """
    Override ``.run()`` and be sure to call ``.done()`` afterwards.

    This is sort of like a future, in that it has a ``result``.
    """

    def __init__(self, pcb, done_cb):
        """
        :param pcb:  Progress callback, which accepts an integer argument and an
                     optional string message indicating progress.
        :param done_cb: Done callback, invoked with the ProgressRunnable as its
                        only argument.
        """
        super().__init__()
        self.pcb = pcb
        self.done_cb = done_cb
        self.result = None
        self.exception = None

    def _run(self):
        raise NotImplementedError

    @pyqtSlot()
    def run(self):
        try:
            self._run()
        except Exception as e:
            self.exception = e
        else:
            self.done()

    def done(self):
        """The default implementation calls ``done_cb(self))``."""
        self.done_cb(self)
