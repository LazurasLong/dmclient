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

The oracle is a separate process that periodically checks the campaign database
for documents. It then attempts to index those documents in a separate thread.
Search queries are read line-by-line from ``stdin`` and return results as a
JSON result object.

The context in which this module is imported and executed is within that
oracle subprocess, _not_ the primary dmclient process.
"""

import importlib
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Thread

import xapian
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from campaign.note import Note
from oracle.index import Indexer

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
            provider_module = importlib.import_module(
                "oracle.provider.{}".format(provider_name))
            providers[provider_name] = provider_module.Provider()
            log.debug("done!")
        except AttributeError:
            log.error("search provider `%s' is unusable (no Provider found)",
                      provider_name)
        except ImportError as e:
            log.error("cannot import search provider `%s': %s", provider_name,
                      e)

    return providers


class OracleDatabase:
    def __init__(self, xdb):
        self.documents = {}
        self.xdb = xdb
        self.lock = Lock()

    @classmethod
    def from_xapian(cls, path):
        # TODO
        xdb = xapian.WritableDatabase(path, xapian.DB_CREATE_OR_OVERWRITE)
        db = cls(xdb)
        return db


class OracleController:
    """
    Mediator and Listener class.
    """
    database_prefix = "dmoracle"
    database_suffix = "xapian.db"

    def __init__(self, oracle_connection, engine, database, providers=None):
        """

        :param oracle_connection: The oracle's connection to Delphi.
        :param engine: An SQLAlchemy engine associated with the campaign
                       database.
        :param database: The ``OracleDatabase`` to work from.
        """
        self.oracle_connection = oracle_connection

        self.campaign_engine = engine
        self.Session = self.create_session(self.campaign_engine)

        self.database = database

        self.notemap = {}
        if not providers:
            providers = {}
        self.providers = providers

        self.executor = ThreadPoolExecutor(max_workers=1)
        self.pending = []
        self.thread = Thread(target=self.exec, name="listener")

    @classmethod
    def create_session(cls, engine):
        return sessionmaker(bind=engine)

    def search(self, *query):
        self.searcher.pending.put(' '.join(query))

    def exec(self):
        conn = self.oracle_connection
        while 1:
            try:
                if conn.poll(2):
                    self.execute_command(conn.recv())
                else:
                    self.sync_notes()
            except EOFError:
                log.error("error: received end-of-file")
                break
            except UnicodeDecodeError as e:
                log.error("error receiving command: %s", e)

    def execute_command(self, cmdstr):
        log.debug("received command: `%s'", cmdstr)
        cmd, *args = cmdstr.split(' ')
        log.debug("got cmd %s(%s)", cmd, args)
        cmd_method = getattr(self, cmd, None)
        if not cmd_method:
            log.error("invalid command `%s'", cmdstr)
            return
        ret = cmd_method(*args)
        if ret:
            log.warning("cmd returned something...")

    def sync_notes(self):
        session = self.Session()
        notes = session.query(Note)
        self.process_notes(notes)

    def process_notes(self, notes):
        notemap = self.notemap
        for note in notes:
            if note.id not in notemap:
                self.index_note(note)

    def index_note(self, note):
        self.notemap[note.id] = None  # FIXME ugh
        indexer = Indexer()
        provider = self.providers[note.type]
        f = self.executor.submit(indexer.index_note, provider, note)
        f.add_done_callback(self.index_complete)
        self.pending.append(f)

    def index_complete(self, f):
        try:
            document, noteid = f.result()
        except Exception as e:
            log.exception("failed to index: %s", e)
        else:
            with self.database.lock:
                self.database.xdb.add_document(document)
            self.notemap[noteid] = document
        finally:
            self.pending.remove(f)


def main(app_args, oracle_args):
    """
    :param app_args: CLI arguments for oracle process
    :param oracle_args: The ``Connection`` object that lets us
                 talk with dmclient proper
    """
    delphi_conn = oracle_args["delphi"]
    engine = create_engine("sqlite:///{}".format(oracle_args["campaign"]))
    database = OracleDatabase.from_xapian(oracle_args["xapian"])
    providers = _load_default_providers()
    controller = OracleController(delphi_conn, engine, database, providers)

    try:
        controller.exec()
    finally:
        delphi_conn.send("hurk dead")

    sys.exit(0)

# TODO
# if __name__ == '__main__':
#     main()
