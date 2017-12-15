# core/archive.py
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

.. note ::
    For whatever reason, ``tarfile`` on Windows uses forward slashes instead
    of ``os.sep``. As a result, this module never makes use of
    ``os.path.join()``.
"""

import io
from json import JSONDecodeError
import os.path
import pathlib
import tarfile
from logging import getLogger

from campaign import Campaign, CampaignSession
from model.schema import *

__all__ = ["load_campaign", "InvalidArchiveError", "InvalidSessionError"]

log = getLogger(__name__)  # TODO archives should not require logging.


class InvalidArchiveError(Exception):
    """Raised when an archive is corrupt or missing essential data."""


class NoSuchDirectoryError(InvalidArchiveError):
    pass


class NoSuchArchiveFileError(InvalidArchiveError):
    pass


class InvalidSessionError(InvalidArchiveError):
    """Raised when a campaign archive contains invalid data."""


def open_expansion(path):
    return None


def open_library(path):
    return Archive.open(path)  # TODO - validate that it's a library.


def load_campaign(path):
    with Archive.open(path) as archive:
        return _make_campaign(archive)


def _make_campaign(archive):
    from core.archive.map import make_maps  # FIXME: hack
    properties = _parse_json(archive.textfile("properties.json"),
                             CampaignPropertiesSchema)
    campaign = Campaign(**properties)

    try:
        loader = NoteLoader()
        campaign.notes = loader.load(archive)
    except Exception as e:
        log.error("campaign notes unavailable: %s", e)

    for sessiondir in archive.subdir("sessions").dirs():
        try:
            campaign.sessions.append(_make_session(sessiondir))
        except InvalidSessionError as e:
            log.error("bad session data: %s", e)

    # try:
    #     mapdir = archive.subdir("maps")
    #     maps = make_maps(mapdir)
    #     print(maps)
    #     campaign.regional_maps = maps
    # except NoSuchDirectoryError:
    #     pass

    return campaign


def _make_session(sessiondir):
    try:
        propfile = sessiondir.textfile("properties.json")
        properties = _parse_json(propfile, SessionPropertiesSchema)
    except (NoSuchArchiveFileError, JSONDecodeError) as e:
        raise InvalidSessionError("non-existent or malformed properties.json!") from e
    try:
        log_contents = sessiondir.textfile("session.log").read()
    except NoSuchArchiveFileError:
        log_contents = ""
    session = CampaignSession(properties["start_time"], log_contents)
    try:
        # TODO: ..
        # 1. (optionally) lazily load, so we can...
        # 2. support any filetype (by opening external program)
        for note in sessiondir.subdir("notes").files():
            if note.name == "properties.json":
                continue
            session.notes[note.name] = note.read()
    except NoSuchDirectoryError:
        log.info("Session {} does not appear to have any notes."
                 .format(sessiondir.name))
    return session


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
            log.debug("validation errors: %s", errors)
            raise JSONDecodeError("schema validation failed", "", 0)
        return obj
    except ValueError:
        raise JSONDecodeError("", "", pos=0)


class NoteLoader:
    def load(self, archive):
        """Return a list of notes."""
        notes = _parse_json(archive.textfile("notes.json"), NoteSchema)
        for note in notes:
            pass


class FileIOWrapper:
    """This class exists because the rest of this code is shitty, and
    io.BufferedReader objects don't have a 'name' attribute when they exist
    from tar archives. We need(?) it, so we store it in this wrapper class.

    """

    def __init__(self, name, bufreader):
        """
        :param: name The full tar archive name. This is truncated to just the
        basename when stored in this class.
        :param: The underlying IO reader we forward calls to.
        """
        self.name = os.path.basename(name)
        self.bufreader = bufreader

    def read(self, size=None):
        return self.bufreader.read(size)


class DirectoryWrapper:
    def __init__(self, archive, prefix):
        self.archive = archive
        self.name = os.path.basename(prefix)  # FIXME is this really needed?
        self.prefix = prefix

    def __repr__(self):
        return "<DirectoryWrapper '%s'>" % self.prefix

    def subdir(self, name):
        """Return a (sub) directory matching a given name."""
        return self.archive.subdir(self.prefix + '/' + name)

    def file(self, name):
        return self.archive.file(self.prefix + '/' + name)

    def textfile(self, name):
        return self.archive.textfile(self.prefix + '/' + name)

    def _is_direct_descendent(self, name):
        path = pathlib.PurePath(name)
        prefixpath = pathlib.PurePath(self.prefix)
        return path.parent == prefixpath

    def dirs(self):
        dirs_ = sorted(
            [dir_.name for dir_ in self.archive._tarfile.getmembers() if
             (dir_.isdir() and self._is_direct_descendent(dir_.name))])
        for dir_ in dirs_:
            yield DirectoryWrapper(self.archive, dir_)

    def _files(self):
        # FIXME hack
        return [file_.name for file_ in self.archive._tarfile.getmembers() if
                file_.isfile() and self._is_direct_descendent(file_.name)]

    def files(self):
        return [self.archive.file(x) for x in self._files()]

    def textfiles(self):
        return [self.archive.textfile(x) for x in self._files()]


class Type:
    unknown = 0
    library = 1
    expansion = 2
    campaign = 3


class Archive:
    """Base class for all archive files.

    Note that we don't provide a dirs() or files() method because that would be
    pointless. Something is doing something wrong if that is the case!

    FIXME: tarfile shouldn't be a parameter, exposes too much.

    """

    def __init__(self, tarfile_, path=None):
        self._tarfile = tarfile_
        self.path = path
        f = self.textfile("properties.json")
        self.properties = _parse_json(f, ArchivePropertiesSchema)

    @classmethod
    def open(cls, path, mode='r'):
        try:
            tarfile_ = tarfile.open(path, "{}:bz2".format(mode))
            return cls(tarfile_, path)
        except (tarfile.ReadError, EOFError):
            raise InvalidArchiveError("Invalid tar file")

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if type is None:
            self.close()

    def close(self):
        self._tarfile.close()

    def is_library(self):
        return False

    def is_campaign(self):
        return False

    def subdir(self, dirname):
        try:
            entry = self._tarfile.getmember(dirname)
        except KeyError:
            raise NoSuchDirectoryError("dir `%s' not found " % dirname)
        if not entry.isdir():
            raise NoSuchDirectoryError("`%s' is not a directory" % dirname)

        return DirectoryWrapper(self, dirname)

    def _file_named(self, name):
        try:
            file = self._tarfile.extractfile(name)
            # FIXME. So we allow symlinks?
            if file is None:
                raise NoSuchArchiveFileError("file is none")
            return file
        except KeyError:
            raise NoSuchArchiveFileError("file `%s' not found" % name)

    def file(self, name):
        reader = self._file_named(name)
        return FileIOWrapper(name, reader)

    def textfile(self, name):
        reader = io.TextIOWrapper(self._file_named(name), encoding="utf-8")
        return FileIOWrapper(name, reader)
