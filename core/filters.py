# core/filters.py
# Copyright (C) 2017 Alex Mair. All rights reserved.
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

"""This module contains filename filters for use in file dialogs.

Since dmclient only supports Qt at the moment this is all very simple.
"""

from core.config import APP_NAME

__all__ = ["join",
           "any", "campaign", "library", "expansion",
           "json", "yaml",
           "png", "gif", "jpeg", "svg", "icon",
           "all_documents", "pdf", "txt", "document",
           ]


def join(*args):
    """Join a list of filters together. Note that whilst ``filters.ANY`` is
    typically located at the last of dialogs, this function does not (currently)
    enforce this.

    """
    return ";;".join(args)


any = "All files (*.*)"
campaign = "%s campaign (*.dmc)" % APP_NAME
library = "%s library (*.dml)" % APP_NAME
expansion = "%s expansion (*.dmx)" % APP_NAME

json = "JSON (*.json)"
yaml = "YAML (*.yaml)"

png = "Portable Network Graphics (*.png)"
gif = "GIF (*.gif)"
jpeg = join("JPEG (*.jpeg)", "JPG (*.jpg)")
svg = "Scalable Vector Graphics (*.svg)"
icon = join(png, gif, jpeg, svg)

all_documents = "All supported document formats (*.pdf, *.txt)"
pdf = "PDF (*.pdf)"
txt = "Plain text (*.txt)"
document = join(all_documents, pdf, txt)
