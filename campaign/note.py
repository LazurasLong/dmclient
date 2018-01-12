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
