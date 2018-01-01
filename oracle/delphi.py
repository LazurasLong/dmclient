# oracle/delphi.py
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
Delphi is the connection to the Oracle process. It is cheekily named: to get
to the oracle, you must first travel to Delphi  :)

.. todo::
    An dmclient-dmoracle is a 1:1 process mapping, but dmclient may need
    multiple connections to the oracle? Implement that one-to-many mapping.

"""
import sys
import threading
from itertools import product
from logging import getLogger
from multiprocessing import Pipe

log = getLogger("delphi")

if __debug__:
    bad_modules = ("PyQt5",)


    def module_sanity_check():
        """
        Ensure that nothing unnecessary makes it into the oracle subprocess
        as a result of the fork.

        For example, the oracle has zero need for PyQt5.

        """
        for module_name, bad_module in product(sys.modules.keys(), bad_modules):
            assert bad_module not in module_name, "{} was in sys.modules ({})".format(
                bad_module, sys.modules)
else:
    def process_sanity_check():
        pass


def delphi_main_thing(args, oracle_connection):
    # FIXME(!!): This isn't working.
    # module_sanity_check()
    # import done here to avoid polluting dmclient's process
    # (it never has any need for stuff like xapian)
    try:
        from .oracle import main as oracle_main
        oracle_main(args, oracle_connection)
    except KeyboardInterrupt:
        sys.exit(0)


class DummyDelphi:
    """
    A stupid Delphi that only returns annoying non-results.

    This class is mostly(?) used when ``--disable-oracle`` is passed on the
    command line. It is also useful when testing, I suppose.

    """

    def __init__(self, *_, **__):
        self.enabled = True
        self.documents = []

    def init_database(self, _, __):
        pass

    def search_query(self, query):
        log.debug("dummy delphi received %s", query)

    def shutdown(self):
        pass


class Delphi:
    """
    .. parsed-literal::
        To talk to the Oracle, you must first go through Delphi.

    *Delphi* represents the dmclient endpoint of the oracle api. It is
    responsible for dispatching search and indexing requests to the oracle
    and handling errors.
    """

    listen_timeout = 1

    def __init__(self, zygote):
        self.zygote = zygote
        self.oracle_pid = None
        self.responder = None
        self.documents = []
        self.keep_going = False
        self.listen_thread = None
        pipe = Pipe()
        self.delphi_connection, self.oracle_connection = pipe

    @property
    def enabled(self):
        """
        :return: ``True`` if the oracle connection is alive and well, ``False``
        otherwise.
        """
        return True

    def index(self, uuid, path):
        log.debug("Delphi requested to index external: (%s, %s)", uuid, path)
        self.responder.indexing_started()

    def search_query(self, query):
        self._send_message("search %s", query)

    def error(self):
        """
        A fatal error occurred on the oracle
        :return:
        """
        self.keep_going = False
        self.responder.on_error()

    def search_completed(self, id, results):
        log.debug("received some completed results for %s: %s", id, results)

    def start(self, campaign_db_path, xapian_db_path, responder):
        self.responder = responder
        self.keep_going = True
        self.listen_thread = threading.Thread(target=self.listen_loop,
                                              name="delphi")
        self.listen_thread.start()
        self.oracle_pid = self.zygote.spawn(
            {"delphi": self.oracle_connection, "campaign": campaign_db_path,
             "xapian": xapian_db_path})
        log.debug("delphi started, spawned oracle PID = %d", self.oracle_pid)

    def shutdown(self):
        log.debug("shutdown triggered")
        self.keep_going = False
        self.listen_thread.join()

    def listen_loop(self):
        log.debug("delphi thread started")
        timeout = self.listen_timeout
        delphi_connection = self.delphi_connection
        while self.keep_going:
            if delphi_connection.poll(timeout):
                obj = delphi_connection.recv()
                log.debug("received `%s' from oracle", obj)

    def _send_message(self, message, *args):
        self.delphi_connection.send(message % args)
