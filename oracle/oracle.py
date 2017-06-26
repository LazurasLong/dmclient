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

"""
This module provides the majority of the implementation of the *oracle*, the
document indexing and searching powered by xapian.

The oracle is a separate process with the following commands available:

* index *document*
* search *query-expr*

The context in which this module is imported and executed is within that
oracle subprocess, _not_ the primary dmclient process.
"""
import importlib
import logging
import os
import sys
from threading import Lock, Thread

import xapian

from core.config import TMP_PATH
from oracle.index import Indexer
from oracle.search import Searcher

log = logging.getLogger("dmoracle")


def _load_default_providers():
    """

    :return: A dictionary of provider-name to provider classes.
    """
    providers = {}
    default_providers = ["pdf"]
    for provider_name in default_providers:
        try:
            log.debug("loading search provider `%s'...", provider_name)
            provider_module = importlib.import_module("oracle.provider.{}"
                                                      .format(provider_name))
            providers[provider_name] = provider_module.Provider()
            log.debug("done!")
        except AttributeError:
            log.error("search provider `%s' is unusable (no Provider found)",
                      provider_name)
        except ImportError as e:
            log.error("cannot import search provider `%s': %s",
                      provider_name, e)

    return providers


class OracleDatabase:
    def __init__(self, xdb):
        self.documents = {}
        self.xdb = xdb
        self.lock = Lock()


class Oracle:
    """
    Mediator and Listener class.
    """
    database_prefix = "dmoracle"
    database_suffix = "xapian.db"

    def __init__(self, delphi_pipe, indexer, searcher):
        self.thread = Thread(target=self.run, name="listener")
        self.delphi_pipe = delphi_pipe
        self.indexer = indexer
        self.searcher = searcher

    #
    # Oracle endpoint implementation.
    #

    def init_database(self, id):
        database_path = self._database_path(id)
        xdb = xapian.WritableDatabase(database_path,
                                      xapian.DB_CREATE_OR_OVERWRITE)
        database = OracleDatabase(xdb)
        self.searcher.database_changed(database)
        self.indexer.database_changed(database)

    def ack(self, ack):
        if ack != "ack":
            log.warning("ack is not ack...")
        out, in_ = self.delphi_pipe
        out.send("hello")

    def index(self, path):
        self.indexer.pending.put(path)

    def search(self, *query):
        self.searcher.pending.put(' '.join(query))

    #
    # Threading magic.
    #

    def run(self):
        out, in_ = self.delphi_pipe
        while 1:
            try:
                cmdstr = in_.recv().decode()
                log.debug("received command: `%s'", cmdstr)

                cmd, *args = cmdstr.split(' ')
                log.debug("got cmd %s(%s)", cmd, args)
                cmd_method = getattr(self, cmd, None)
                if not cmd_method:
                    log.error("invalid command `%s'", cmdstr)
                    continue
                if cmd_method(*args):
                    log.warning("cmd returned something...")
            except EOFError:
                log.error("error: received end-of-file")
                break
            except UnicodeDecodeError as e:
                log.error("error receiving command: %s", e)

    #
    # Helper methods
    #

    @classmethod
    def _database_path(cls, id):
        database_name = "{}-{}-{}".format(cls.database_prefix,
                                          id,
                                          cls.database_suffix)
        return os.path.join(TMP_PATH, database_name)


def oracle_main(args, delphi_pipe):
    stemmer = xapian.Stem("english")

    providers = _load_default_providers()

    indexer = Indexer(stemmer, providers)
    searcher = Searcher(stemmer)
    listener = Oracle(delphi_pipe, indexer, searcher)

    try:
        indexer.thread.start()
        searcher.thread.start()
        listener.thread.start()
    finally:
        listener.thread.join()
        searcher.thread.join()
        indexer.thread.join()

    sys.exit(0)
