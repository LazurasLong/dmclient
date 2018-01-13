# oracle/__init__.py
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

from logging import getLogger

from core.zygote import Zygote
from oracle.delphi import Delphi, DummyDelphi, delphi_main_thing

__all__ = ["spawn_oracle", "spawn_zygote"]

log = getLogger("delphi")


def spawn_zygote(args):
    """
    :param args: arguments to construct the oracle zygote with
    :return: A zygote that can be passed into ``spawn_oracle()``.
    """
    zygote = Zygote(target=delphi_main_thing, name="dmoracle", args=args)
    zygote.capture()
    log.debug("zygote spawned, pid = %d", zygote.pid)
    return zygote


def spawn_oracle(zygote, args):
    """Spawns an Oracle sub-process by forking the current process.

    :return: An instance of the `Delphi` class.
    """

    if args.disable_oracle:
        log.info("The oracle remains silent today...")
        return DummyDelphi(args)

    delphi = Delphi(args)
    delphi.start()
    return delphi
