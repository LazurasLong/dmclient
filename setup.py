# setup.py
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

"""cx_Freeze setup support.

We package for the following platforms in here:

    - Windows (TODO)
    - OS X
"""

import sys

from cx_Freeze import setup, Executable

from core.config import APP_NAME, APP_DESCRIPTION, APP_VERSION

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os"], "excludes": ["tkinter"]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(name=APP_NAME, version=APP_VERSION, description=APP_DESCRIPTION,
      options={"build_exe": build_exe_options},
      executables=[Executable("dmclient.py", base=base)])
