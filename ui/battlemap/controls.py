# ui/battlemap/controls.py
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

from PyQt5.QtWidgets import QGraphicsView


class ControlScheme:
    def __init__(self):
        self.view_anchor = QGraphicsView.AnchorUnderMouse

        """If True, then the mouse wheel zooms in and out. Otherwise it
        manipulates the scroll bars per default Qt settings."""
        self.wheel_zooms = True
