# core/__init__.py
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

"""TODO - write documentation for this module. It seems like it's rapidly
going away...

"""

import string
from uuid import uuid4, UUID


__all__ = ["InvalidUUIDError",
           "UUID",
           "attrs",
           "deurlify",
           "generate_uuid",
           "hrname",
           ]


class InvalidUUIDError(Exception):
    def __init__(self, uuid):
        self.uuid = uuid

    def __str__(self):
        return "invalid UUID %s" % self.uuid


def attrs(obj):
    """Return a dictionary generator containing a ``name`` to ``attr`` mapping
    for the given object ``obj``. Attributes beginning with ``__`` are ignored.

    """
    return {attr: value for attr, value in obj.__dict__.items()
            if not attr.startswith("__")}


def deurlify(url):
    """This function turns local filesystem URLs into a regular file path.
    Raises ValueError if "url" does not begin with "file://"

    By default, local paths from Cocoa come in the form of URLs. This causes
    Python filesystem functions to fail as they expect UNIX-style pathnames.
    """
    if not url.startswith("file://") or len(url) <= len("file://"):
        raise ValueError("`%s' is not a local file URL" % url)
    return url[7:]


generate_uuid = uuid4


def hrname(s):
    """Turns underscores into spaces and then capitalises each word in the
    string.

    For example::

       >>> hrname("foo bar")
       'Foo Bar'
       >>> hrname("foo_bar")
       'Foo Bar'

    """
    return string.capwords(s.replace('_', ' '))


def hrlowername(s):
    """Turns underscores into spaces.

    For example::

        >>> hrlowername("Foo Bar")
        'foo bar'
        >>> hrlowername("foo_bar")
        'foo bar'
    """
    return s.replace('_', ' ').lower()

