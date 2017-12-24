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
import queue
from logging import getLogger
from threading import Thread

import xapian

log = getLogger(__name__)


class IndexWatchdog:
    """
    This class monitors documents held by the indexer and pushes them onto the
    indexing queue if they are found to be out-of-date.
    """
    def __init__(self):
        self.thread = Thread(target=self.run, name="indexer-watchdog")

    def run(self):
        pass


class Indexer:
    def __init__(self, stemmer, providers):
        """

        :param stemmer:
        :param providers:  A dictionary of ``document-type`` to ``Provider``
                           instances that this indexer may use to extract
                           document text from.
        """
        self.term_generator = xapian.TermGenerator()
        self.term_generator.set_stemmer(stemmer)
        self.stemmer = stemmer
        self.providers = providers

        self.thread = Thread(target=self.run, name="indexer")
        self.pending = queue.Queue()

        self.database = None
        self.keep_going = True

    def database_changed(self, database):
        # FIXME this is going to cause a race condition if the db changes
        # whilst we are searching for something......
        self.database = database

    def run(self):
        while self.keep_going:
            try:
                document = self.pending.get(timeout=1)
                try:
                    provider = self.providers[document.type]
                except KeyError:
                    log.error("no provider `%s' for document `%s'",
                              document.type, document.id)
                else:
                    try:
                        text = provider.extract_document_text(document)
                        self._index_document_text(text)
                    except xapian.Error as e:
                        log.error("xapian error whilst indexing `%s': %s",
                                  document, e)
            except queue.Empty:
                pass

    def _index_document_text(self, text):
        document = xapian.Document()
        document.set_data(text)
        self.term_generator.set_document(document)
        self.term_generator.index_text(text)
        with self.database.lock:
            self.database.xdb.add_document(document)
