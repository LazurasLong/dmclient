# core/archive.py
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

.. note ::
    For whatever reason, ``tarfile`` on Windows uses forward slashes instead
    of ``os.sep``. As a result, this module never makes use of
    ``os.path.join()``.
"""

import os
import tarfile
from json import JSONDecodeError

from io import BytesIO
from sqlalchemy import Column, String

from model import DescribableMixin, GameBase
from model.schema import *

__all__ = ["InvalidArchiveError", "InvalidSessionError", "ArchiveMeta",
           "InvalidArchiveMetadataError", "open", "open_campaign",
           "update_archive", "export", "unpack"]

_open = open


class InvalidArchiveError(Exception):
    """Raised when an archive is corrupt or missing essential data."""


class NoSuchDirectoryError(InvalidArchiveError):
    pass


class NoSuchArchiveFileError(InvalidArchiveError):
    pass


class InvalidSessionError(InvalidArchiveError):
    """Raised when a campaign archive contains invalid data."""


def open_campaign(path):
    return open(path)


def open(path):
    return ArchiveMeta.load(path)


def unpack(meta, destination):
    with tarfile.open(meta.last_seen_path, "r:bz2") as f:
        f.extractall(destination)


def export(meta, src, dst):
    """
    Export an archive's contents. Suitable for ``Save as`` operations.

    :param meta: The archive meta.
    :param src: The source working directory to package into an archive.
    :param dst: The destination filename to export to.
    """
    if not src.endswith('/'):
        src += '/'
    with tarfile.open(dst, mode="w:bz2") as tf:
        schema = ArchiveMetaSchema()
        json = str(schema.dumps(meta).data).encode()
        ti = tarfile.TarInfo("properties.json")
        ti.size = len(json)
        tf.addfile(ti, fileobj=BytesIO(json))
        for (dirpath, dirnames, filenames) in os.walk(src):
            for dirname in dirnames:
                tf.add(os.path.join(dirpath, dirname), dirname)
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                tf.add(full_path, filename)
            # Hacky? Tarfile recursively adds the dirs.
            break


class ArchiveMeta:
    def __init__(self, id, game_system_id, name="", description="", author="",
                 creation_date=None, revision_date=None, isbn=None,
                 last_seen_path=None):
        self.id = id
        self.game_system_id = game_system_id
        self.name = name
        self.description = description
        self.author = author
        self.creation_date = creation_date
        self.revision_date = revision_date
        self.isbn = isbn
        self.last_seen_path = last_seen_path

    def __eq__(self, other):
       return self.id == other.id

    @classmethod
    def load(cls, path):
        """
        :return: An ``ArchiveMeta`` instance.
        :raises: InvalidArchiveMetadataError
        """
        try:
            with tarfile.open(path, "r:bz2") as tf:
                meta = _parse_json(tf.extractfile("properties.json"),
                                   ArchiveMetaSchema)
                meta.last_seen_path = path
                return meta
        except JSONDecodeError as e:
            raise InvalidArchiveMetadataError("invalid meta: %s" % e)
        except (tarfile.ReadError, EOFError, JSONDecodeError) as e:
            raise InvalidArchiveError("corrupt archive: %s" % e)


class ArchiveMetaSchema(Schema):
    """
    This schema stores the specification for the toplevel ``properties.json``
    found in an archive.
    """

    class Meta:
        ordered = True

    id = fields.UUID(required=True)
    game_system_id = fields.Str(required=True)
    name = fields.Str(default="")
    description = fields.Str(default="")
    author = fields.Str(default="")
    creation_date = fields.DateTime(format="iso")
    revision_date = fields.DateTime(format="iso")
    isbn = fields.Str(default="")

    @post_load
    def make_meta(self, m):
        return ArchiveMeta(**m)


def _parse_json(f, schemacls):
    """
    :param f: file-like object to read json from
    :param schemacls: the schema to parse the properties with
    :return: a dictionary containing the validated object
    :raises: JSONDecodeError if the JSON is malformed
    """
    schema = schemacls()
    try:
        obj, errors = schema.loads(f.read())
        if errors:
            raise JSONDecodeError("schema validation failed {}".format(errors),
                                  "", 0)
        return obj
    except ValueError as e:
        raise JSONDecodeError("failed to decode JSON: {}".format(e), "", pos=0)


class InvalidArchiveMetadataError(InvalidArchiveError):
    pass


class ArchiveMetaSql(GameBase, DescribableMixin):
    __tablename__ = "archives"

    isbn = Column(String)

    def __init__(self, tarfile, path):
        """

        :param tarfile:
        :param path: Because tarfile is wonderful and doesn't keep it.
        """
        self.tarfile = tarfile
        self.path = path
