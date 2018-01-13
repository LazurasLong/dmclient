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
