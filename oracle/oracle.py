# oracle/oracle.py
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

"""This module provides the majority of the implementation of the
Oracle. Some refactoring is probably required at some point, as this
thing is expected to get huge.

"""

import logging
import os
import subprocess
import sys
from queue import Queue
from threading import Thread, Lock

import xapian

from core.config import TMP_PATH
from oracle.index import Indexer

log = logging.getLogger("dmoracle")

SEARCH_DATABASE_NAME = "dmoracle-xapian.db"


def pdf2txt(source_name, destination_file):
    return subprocess.call(["pdf2txt.py", source_name], stdout=destination_file)


def create_or_open_database(override_path=None):
    path = override_path if override_path is not None \
        else os.path.join(TMP_PATH, SEARCH_DATABASE_NAME)
    return xapian.WritableDatabase(path, xapian.DB_CREATE_OR_OVERWRITE)  # TODO


class Listener:
    def __init__(self, connection, indexer, searcher):
        self.thread = Thread(target=self.run, name="listener")
        self.connection = connection

        self.indexer = indexer
        self.searcher = searcher

    def run(self):
        while 1:
            try:
                cmdstr = self.connection.recv().decode()
                log.debug("received command: `%s'", cmdstr)

                cmd, *args = cmdstr.split(' ')
                log.debug("got cmd %s(%s)", cmd, args)
                if getattr(self, cmd)(*args):
                    log.warning("cmd returned something...")
            except EOFError:
                log.error("error: received end-of-file")
                break
            except UnicodeDecodeError as e:
                log.error("error receiving command: %s", e)
            except (AttributeError, TypeError, ValueError) as e:
                log.error("invalid command `%s': %s", cmdstr, e)

    def ack(self, ack):
        if ack != "ack":
            log.warning("ack is not ack...")
        self.connection.send("hello")

    def index(self, path):
        self.indexer.pending.put(path)

    def search(self, *query):
        self.searcher.pending.put(' '.join(query))


class Searcher:
    def __init__(self, database, database_lock, indexer, stemmer, query_parser):
        self.database = database
        self.database_lock = database_lock
        self.thread = Thread(target=self.run, name="searcher")
        self.pending = Queue()
        self.indexer = indexer
        self.stemmer = stemmer
        self.query_parser = query_parser

    def run(self):
        while 1:
            query = self.pending.get()
            with self.database_lock:
                self.print_results(query)

    def print_results(self, query):
        enquire = xapian.Enquire(self.database)
        query = self.query_parser.parse_query(query)
        enquire.set_query(query)
        matches = enquire.get_mset(0, 10)
        print("%d results found" % matches.get_matches_estimated())
        for m in matches:
            print("\t{}: {}%% docid={}\n\t\t{}".format(m.rank, m.percent,
                                                       m.docid,
                                                       m.document.get_data()))


def oracle_main(args, pipe):
    database = create_or_open_database()
    database_lock = Lock()

    delphiout, delphiin = pipe

    stemmer = xapian.Stem("english")

    indexer = xapian.TermGenerator()
    indexer.set_stemmer(stemmer)

    query_parser = xapian.QueryParser()
    query_parser.set_stemmer(stemmer)
    query_parser.set_database(database)
    query_parser.set_stemming_strategy(xapian.QueryParser.STEM_SOME)

    indexer = Indexer(database, database_lock, indexer, stemmer)
    searcher = Searcher(database, database_lock, indexer, stemmer, query_parser)
    listener = Listener(delphiin, indexer, searcher)

    try:
        indexer.thread.start()
        searcher.thread.start()
        listener.thread.start()
    finally:
        listener.thread.join()
        searcher.thread.join()
        indexer.thread.join()

    sys.exit(0)
