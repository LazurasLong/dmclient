# campaign/note.py
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

"""
Document management. Roleplaying games tend to involve a lot of notetaking,
in a variety of formats such as plain-text, PDF, or DOCX.
"""
import os
from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy import Column, String, ForeignKey, Integer

from model import GameBase


class Note(GameBase):
    __tablename__ = "note"

    id = Column(Integer, primary_key=True)
    name = Column(String, default="Untitled Note")
    author = Column(String)
    url = Column(String)

    def __str__(self):
        return self.name

    @property
    def type(self):
        return urlparse(self.url).scheme


class InternalNote(GameBase):
    """
    Internal notes are just plain-text, which is why they have a text entry.
    """
    __tablename__ = "internal_note"

    id = Column(Integer, primary_key=True)
    note_id = Column(Integer, ForeignKey('note.id'))
    text = Column(String)
