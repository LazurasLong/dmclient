#!/usr/bin/env python3.6
# dmoracle.py
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

"""This module provides an interactive oracle prompt."""
import os

from dmclient import init_logging, CONFIG_PATH
from oracle import spawn_oracle


def main():
    class OracleArgs:
        logfile = os.path.join(CONFIG_PATH, "dmoracle.log")
    init_logging(OracleArgs)

    delphi = spawn_oracle(None)
    try:
        while 1:
            text = input("Enter command (? for help): ")
            if not text:
                continue
            elif text == "quit":
                break
            delphi.send_message(text)
    except KeyboardInterrupt:
        pass
    except EOFError:
        pass
    finally:
        delphi.shutdown()
        print("Goodbye.")


if __name__ == "__main__":
    main()
