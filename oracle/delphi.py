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

"""Delphi is the connection to the Oracle process. It is cheekily named: to get
to the oracle, you must first travel to Delphi  :)

.. todo::
    An dmclient-dmoracle is a 1:1 process mapping, but dmclient may need
    multiple connections to the oracle? Implement that one-to-many mapping.

"""
import threading
from itertools import product
from logging import getLogger

import sys

from multiprocessing import Pipe

from multiprocessing import Process

log = getLogger("delphi")

if __debug__:
    bad_modules = ["PyQt5", ]


    def module_sanity_check():
        """Ensure that nothing unnecessary makes it into the oracle subprocess
        as a result of the fork.

        For example, the oracle has zero need for PyQt5.

        """
        for module_name, bad_module in product(sys.modules.keys(), bad_modules):
            assert bad_module not in module_name, "{} was in sys.modules ({})".format(
                    bad_module, sys.modules)
else:
    def process_sanity_check():
        pass


def delphi_main_thing(args, pipe):
    module_sanity_check()
    # import done here to avoid polluting dmclient's process
    # (it never has any need for stuff like xapian)
    from .oracle import oracle_main
    oracle_main(args, pipe)


class DummyDelphi:
    """A stupid Delphi that only returns annoying non-results.

    This class is mostly(?) used when ``--disable-oracle`` is passed on the
    command line. It is also useful when testing, I suppose.

    """

    def __init__(self):
        self.search_callback = None
        pass

    def send_search_query(self, query):
        if not self.search_callback:
            return
        error_results = {"Warning": ["The Oracle is not available."]}
        self.search_callback(error_results)

    def shutdown(self):
        pass


class Delphi:
    """To talk to the Oracle, you must first go through Delphi."""

    TIMEOUT = 1  # seconds

    def __init__(self, args):
        self.documents = []
        self.keep_going = False
        self.listen_thread = threading.Thread(target=self.run, name="delphi")
        pipe = Pipe()
        self.oraclein, self.oracleout = pipe
        self.oracle = Process(target=delphi_main_thing, name="dmoracle",
                              args=(args, pipe))

    def index_external_document(self, uuid, path):
        log.debug("Delphi requested to index external: (%s, %s)", uuid, path)

    def start(self):
        self.keep_going = True
        self.listen_thread.start()
        self.oracle.start()
        log.debug("delphi started, oracle PID = %d" % self.oracle.pid)

    def send_message(self, message, *args):
        encoded_message = (message % args).encode()
        self.oraclein.send(encoded_message)

    def shutdown(self):
        log.debug("shutdown triggered")
        self.keep_going = False
        self.listen_thread.join()
        self.oracle.terminate()
        self.oracle.join()

    def run(self):
        log.debug("delphi thread started")
        oraclein = self.oraclein
        while self.keep_going:
            if oraclein.poll(self.TIMEOUT):
                obj = oraclein.recv()
                log.debug("received `%s' from oracle", obj)
