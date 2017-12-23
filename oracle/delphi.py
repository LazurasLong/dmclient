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
import signal
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from itertools import product
from logging import getLogger
from multiprocessing import Pipe, Process

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
            assert bad_module not in module_name, \
                "{} was in sys.modules ({})".format(bad_module, sys.modules)
else:
    def process_sanity_check():
        pass


class Zygote:
    """
    A captured state of a process that is suitable for forking multiple times.

    The oracle is expected to choke on PDF inputs now and then, and it also
    makes sense to spin up a restartable process separate from the main one.
    """

    def __init__(self, target, args, name):
        self.target = target
        self.name = name
        self.args = args
        # Delphi state
        self.egg = None
        self.egg_pipe = None
        # Zygote state
        self.current_spawn = None

    def capture(self, oracle_connection):
        """
        Capture the current state of the process, forking off a new child
        with which to communicate.
        """
        self.egg_pipe = Pipe()
        self.egg = Process(target=self.zygote_main,
                           name="{} Zygote".format(self.name),
                           args=(self.egg_pipe[1], oracle_connection))
        self.egg.start()
        return self.egg.pid

    def spawn(self):
        """
        This method causes the zygote to fork a new process.

        This blocks until that process is created, and returns its PID.
        """
        self.egg_pipe[0].send("spawn")
        return self.egg_pipe[0].recv()

    def kill(self):
        self.egg.terminate()
        self.egg.join()

    def zygote_main(self, egg_connection, oracle_connection):
        dispatch = lambda sig, frame: self.zygote_sighandler(sig, frame)
        signal.signal(signal.SIGTERM, dispatch)
        signal.signal(signal.SIGSEGV, dispatch)
        try:
            while 1:
                if egg_connection.poll(1):
                    cmd = egg_connection.recv()
                    if cmd != "spawn":
                        print("not sure what to do with this command.")
                        continue
                    pid = self.zygote_spawn(oracle_connection)
                    egg_connection.send(pid)
        except KeyboardInterrupt:
            egg_connection.send("told to quit")

    def zygote_spawn(self, oracle_connection):
        if self.current_spawn and self.current_spawn.is_alive():
            log.error("asked to spawn when current is still alive!")
            return
        self.current_spawn = Process(target=self.target,
                                     name=self.name,
                                     args=(self.args, oracle_connection))
        self.current_spawn.start()
        return self.current_spawn.pid

    def zygote_sighandler(self, signum, frame):
        if signum == signal.SIGSEGV:
            print("seg fault in zygote", file=sys.stderr)
            sys.exit(1)
        elif signum == signal.SIGTERM:
            print("goodbye")
            sys.exit(0)
        else:
            print("error: i don't know what to do", file=sys.stderr)
            sys.exit(2)


def delphi_main_thing(args, oracle_connection):
    module_sanity_check()
    # import done here to avoid polluting dmclient's process
    # (it never has any need for stuff like xapian)
    try:
        from .oracle import oracle_main
        oracle_main(args, oracle_connection)
    except KeyboardInterrupt:
        sys.exit(0)


class DummyDelphi:
    """
    A stupid Delphi that only returns annoying non-results.

    This class is mostly(?) used when ``--disable-oracle`` is passed on the
    command line. It is also useful when testing, I suppose.

    """

    def __init__(self, args=None):
        """

        :param args:  Unused.
        """
        self.enabled = True
        self.documents = []

    def init_database(self, id):
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

    def __init__(self, responder):
        """

        :param responder: A listener object that accepts the following::
            indexing_started()
            indexing_completed()
            results_updated()
            on_error()
        """
        self.responder = responder
        self.documents = []
        self.keep_going = False
        self.listen_thread = None
        pipe = Pipe()
        self.delphi_connection, self.oracle_connection = pipe
        self.zygote = Zygote(target=delphi_main_thing, name="dmoracle",
                             args=(pipe,))

    @property
    def enabled(self):
        """
        :return: ``True`` if the oracle connection is alive and well, ``False``
        otherwise.
        """
        return True

    #
    # oracle API dispatch.
    #

    def init_database(self, id):
        self._send_message("init_database %s", id)

    def index(self, uuid, path):
        log.debug("Delphi requested to index external: (%s, %s)", uuid, path)
        self.responder.indexing_started()

    def search_query(self, query):
        self._send_message("search %s", query)

    #
    # Delphi endpoint methods.
    #

    def error(self):
        """
        A fatal error occurred on the oracle
        :return:
        """
        self.keep_going = False
        self.responder.on_error()

    def search_completed(self, id, results):
        log.debug("receieved some completed results for %s: %s", id, results)

    #
    # Delphi thread methods.
    #

    def start(self):
        self.keep_going = True
        pid = self.zygote.capture(self.oracle_connection)
        self.listen_thread = threading.Thread(target=self.listen_loop,
                                              name="delphi")
        self.listen_thread.start()
        log.debug("delphi started, zygote oracle PID = %s" % pid)
        oracle_pid = self.zygote.spawn()
        log.debug("spawned oracle PID = %s", oracle_pid)

    def shutdown(self):
        log.debug("shutdown triggered")
        self.keep_going = False
        self.listen_thread.join()
        self.zygote.kill()

    def listen_loop(self):
        log.debug("delphi thread started")
        timeout = self.listen_timeout
        delphi_connection = self.delphi_connection
        while self.keep_going:
            if delphi_connection.poll(timeout):
                obj = delphi_connection.recv()
                log.debug("received `%s' from oracle", obj)

    #
    # Helper methods
    #

    def _send_message(self, message, *args):
        encoded_message = (message % args).encode()
        self.delphi_connection.send(encoded_message)
