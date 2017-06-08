# oracle/index.py
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

"""Classes and functions for indexing search providers."""

from logging import getLogger
from queue import Queue
from threading import Thread

import xapian

log = getLogger(__name__)


class Document:
    pass


class DocumentMetadata:
    def __init__(self):
        self.title = None
        self.author = None
        self.last_modified = None


class Indexer:
    def __init__(self, database, database_lock, indexer, stemmer):
        self.database = database
        self.database_lock = database_lock
        self.indexer = indexer
        self.stemmer = stemmer

        self.thread = Thread(target=self.run, name="indexer")
        self.pending = Queue()

        self.providers = []

    def run(self):
        while 1:
            path = self.pending.get()
            try:
                log.debug("indexing...")
                self.index_pdf(path)
                log.debug("done")
            except xapian.Error as e:
                log.error("xapian error whilst indexing `%s': %s", path, e)

    def index_document(self, text):
        with self.database_lock:
            document = xapian.Document()
            document.set_data(text)
            self.indexer.set_document(document)
            self.indexer.index_text(text)
            self.database.add_document(document)
