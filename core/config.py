# core/config.py
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

"""This module provides dmclient some meta-related pieces of information, such
as characteristics of the program itself, and values that may differ from
platform-to-platform. These two categories are explained in their appropriate
subsections below.

This module is also used by many of the tool scripts located in `scripts/`
directory, and most importantly, `setup.py`. This allows those scripts to
generate non-Python-code based resources (e.g. the Windows executable) with the
correct pieces of information.

.. todo::
    "Parameters" really isn't the best word.

.. todo::
    Auto-generate some or all of this file based on a template. `APP_BUILD` and
    `APP_BUILD_DATE` should be updated when the necessary build requirements are
    executed (e.g., generating Python classes from the .ui files for Qt)

.. todo::
    Finish documenting this module!

Application specific parameters
===============================
This includes the following:

.. data:: APP_NAME
    The userland (i.e. visible) name of the application. This appears in all GUI
    forms where required.

.. data:: APP_VERSION
    A string of the form `X.Y.Z` containing dmclient's version identifier.

.. data:: APP_VERSION_NAME
    A string containing a natural language

"""

# TODO - generate this file automatically (or at least parts of it)
# TODO - automatically inline the vars in this file so we don't have to do lookup or global references

import os
import platform


APP_NAME = "dmclient"
APP_DOMAIN = "ca.theshrine."

if platform.system() == "Windows":
    HOMEPATH = os.path.expandvars('$USERPROFILE')
    APP_PATH = os.path.join(os.path.expandvars("%AppData%"), APP_NAME)
    TMP_PATH = os.path.join(APP_PATH, "tmp")
    CONFIG_PATH = os.path.join(APP_PATH, "config")
    CAMPAIGN_PATH = os.path.join(APP_PATH, "Campaigns")
elif platform.system() == "Darwin":
    HOMEPATH = os.path.expandvars('$HOME')
    APP_PATH = os.path.join(HOMEPATH, "Library", "Application Support", APP_NAME)
    TMP_PATH = os.path.join(HOMEPATH, "Library", "Caches", APP_DOMAIN + APP_NAME)
    CONFIG_PATH = os.path.join(HOMEPATH, "Library", "Preferences", APP_DOMAIN + APP_NAME)
    CAMPAIGN_PATH = os.path.join(APP_PATH, "Campaigns")
elif platform.system() == "Linux":
    HOMEPATH = os.path.expandvars('$HOME')
    CONFIG_PATH = os.path.join(HOMEPATH, ".config", APP_NAME)
    APP_PATH = CONFIG_PATH
    TMP_PATH = os.path.join(CONFIG_PATH, "tmp")
    CAMPAIGN_PATH = TMP_PATH
else:
    raise NotImplementedError("Support for your platform does not exist.")

# This folder is expected to be in:
#  o  the shared dmclient installation location (ProgramFiles, /Applications &c)
#  o  the user's local directory for dmclient
RESOURCE_DIR = "resources"
APP_BUILD = "d34db33f"
APP_BUILD_DATE = "2112-01-01"
APP_VERSION = "0.0.1"
APP_VERSION_NAME = "Prerelease Pixie"
APP_VERSION_DATE = "SOME_DATE"
APP_DESCRIPTION = "a tool to ease the computational aspects " \
                  "of table-top role-playing games"
APP_URL = "http://theshrine.ca/dmclient/"
BUG_URL = APP_URL + "bugreport.py"
DONATE_URL = "http://theshrine.ca/donate.py"
APP_ICON_PATH = os.path.join(RESOURCE_DIR, "logo.png")
LICENSE_NAGGING = """To use the contents of this {0} archive, you must agree to the terms of the license

Click Agree to continue, or click Disagree to cancel the inclusion of this {0} archive.
""".format(APP_NAME)

# This definitely needs to be generated externally, even depending on the build!
# e.g. Debian build vs source build
HAS_EXTERNAL_UPDATER = False


copyright = "Copyright (C) 2018 Alex Mair. All rights reserved."


class AppConfig:
    def __init__(self):
        self.open_last_campaign = False
        self.last_campaign_path = ""
        self.recent_dirs = {}

    def update(self, source):
        for attr in [attr for attr in self.__dict__ if
                     not attr.startswith("__")]:
            try:
                assert isinstance(source[attr], type(getattr(self, attr)))
                setattr(self, attr, source[attr])
            except KeyError:
                pass


_appconfig = AppConfig()


def appconfig():
    global _appconfig
    return _appconfig
