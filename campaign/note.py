"""
Document management. Roleplaying games tend to involve a lot of notetaking,
in a variety of formats such as plain-text, PDF, or DOCX.
"""
from datetime import datetime

import os
from sqlalchemy import Column, String, ForeignKey, Integer

from model import GameBase


class Note(GameBase):
    __tablename__ = "note"

    id = Column(Integer, primary_key=True)
    name = Column(String, default="Untitled Note")
    author = Column(String)

    def __str__(self):
        return self.name


class InternalNote(GameBase):
    __tablename__ = "internal_note"

    id = Column(Integer, primary_key=True)
    note_id = Column(Integer, ForeignKey('note.id'))
    text = Column(String)


class ExternalNote(GameBase):
    """
    A ``NoteReference`` is a note external to dmclient on some provider, such as
    the local filesystem or a cloud storage service.

    This class is abstract.
    """
    __tablename__ = "external_note"

    id = Column(Integer, primary_key=True)
    note_id = Column(Integer, ForeignKey('note.id'))
    url = Column(String)

    @property
    def creation_date(self):
        raise NotImplementedError

    @property
    def revision_date(self):
        raise NotImplementedError


class DinosaurNote(ExternalNote):
    """
    For those old fogies that still like using their local filesystem to store
    things.  :)
    """

    @property
    def creation_date(self):
        # FIXME oh the great debate. This isn't right on UNIX.
        return datetime.fromtimestamp(os.stat(self.url).st_ctime)

    @property
    def revision_date(self):
        return datetime.fromtimestamp(os.stat(self.url).st_mtime)
