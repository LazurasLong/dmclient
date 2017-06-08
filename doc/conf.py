# doc/conf.py
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

"""Sphinx configuration file."""

from core import config

exclude_patterns = ["**/.git",
                    "**/icons_rc.py",
                    "ui/widgets/*.py"]
needs_sphinx = '1.2'
nitpicky = True
# This is temp for now.
rst_epilog = """
.. |tsdotca| replace:: theshrine.ca
"""

project = config.APP_NAME
copyright = config.copyright
version = config.APP_VERSION
release = version

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.pngmath",
    "sphinx.ext.ifconfig",
    "sphinx.ext.viewcode",
]

html_theme = "default"
