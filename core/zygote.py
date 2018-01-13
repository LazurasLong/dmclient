# core/zygote.py
# Copyright (C) 2018 Alex Mair. All rights reserved.
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
A *zygote* is a captured state of a process that is suitable for forking
multiple times as a "cloned child" of the zygote, called an *egg* or *spawned
egg*. The *client* is the original host process that communicates with the eggs
to perform useful tasks.

Zygotes do not clean up their spawned eggs, instead ownership is
implicitly transferred upon creation.
"""

import os
import signal
import sys
from logging import getLogger
from multiprocessing import Pipe, Process

log = getLogger("zygote")


class Zygote:
    """
    A class suitable for capturing and recreating process state.
    """

    def __init__(self, target, args, name):
        """

        :param target: The "main" method that spawned eggs will run. It must
            take two arguments: the application ``args`` and the pipe with which
            it may send and receive messages from the client.
        :param args: App args.
        :param name: A debugging identifier for the zygote process.
        """
        self.target = target
        self.name = name
        self.app_args = args
        # Client state
        self.egg = None
        self.egg_pipe = None
        # Zygote state FIXME
        self.current_spawn = None
        self.respawn_tries = 0

    @property
    def enabled(self):
        return not self.app_args.disable_oracle

    @property
    def pid(self):
        return self.egg.pid

    def capture(self):
        """
        Capture the current state of the process, forking off a new child
        with which to communicate.
        """
        self.egg_pipe = Pipe()
        self.egg = Process(target=self._zygote_main,
                           name="{} Zygote".format(self.name),
                           args=(self.egg_pipe[1],))

        self.egg.start()

    def spawn(self, args):
        """
        This method causes the zygote to fork a new process.

        This blocks until that process is created, and returns its PID.
        """
        args.update({"cmd": "spawn"})
        self.egg_pipe[0].send(args)
        return self.egg_pipe[0].recv()

    def kill(self):
        self.egg_pipe[0].send({"cmd": "quit"})
        self.egg.join()

    def _zygote_main(self, eggconn):
        return sys.exit(self.zygote_main(eggconn))

    def zygote_main(self, eggconn):  # FIXME delphi hack
        """

        :param eggconn:
        """
        sighandler = lambda sig, frame: self.zygote_sighandler(sig, frame)
        for sig in (signal.SIGTERM, signal.SIGSEGV):
            signal.signal(sig, sighandler)
        try:
            while 1:
                if eggconn.poll(1):
                    thing = eggconn.recv()
                    cmd = thing.pop("cmd")
                    if cmd == "quit":
                        if self.current_spawn:
                            os.kill(self.current_spawn.pid, signal.SIGTERM)
                            self.current_spawn.join()
                        return 0
                    elif cmd == "spawn":
                        assert "delphi" in thing
                        self.zygote_spawn(eggconn, thing)
                    else:
                        log.warning("not sure what to do with this command.")
                        continue
                if self.current_spawn and not self.current_spawn.is_alive():
                    log.warning("I detected dead eggs")
                    # TODO: establish a reconnection from main process
                    self.current_spawn = None
        except KeyboardInterrupt:
            eggconn.send("told to quit")

    def zygote_spawn(self, eggconn, spawn_args):
        if self.current_spawn and self.current_spawn.is_alive():
            log.error("asked to spawn when current is still alive!")
            return
        self.current_spawn = Process(target=self.target, name=self.name,
                                     args=(self.app_args, spawn_args))
        self.current_spawn.start()
        eggconn.send(self.current_spawn.pid)

    def zygote_sighandler(self, signum, frame):
        if signum == signal.SIGSEGV:
            log.fatal("seg fault in zygote", file=sys.stderr)
            sys.exit(1)
        elif signum == signal.SIGTERM:
            log.info("got SIGTERM")
            sys.exit(0)
        else:
            log.fatal("i don't know what to do", file=sys.stderr)
            sys.exit(2)
