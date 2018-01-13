"""Tests for the campaign archive structure."""
import tarfile

import pytest
from dateutil.parser import parse as dtparse

from core import archive
from core.archive import InvalidArchiveError, InvalidArchiveMetadataError, \
    ArchiveMetaSchema


@pytest.fixture(scope="module")
def archive_meta():
    return archive.ArchiveMeta.load("resources/test/protege/testcampaign.dmc")


def test_loading_metadata(archive_meta):
    assert "PROTEGE" == archive_meta.game_system_id
    assert "PROTéGé Test Campaign" == archive_meta.name
    assert "Alex Mair" == archive_meta.author
    assert dtparse("2016-04-20") == archive_meta.creation_date
    assert dtparse("2016-04-21") == archive_meta.revision_date
    assert "978-3-16-148410-0" == archive_meta.isbn
    assert "This is a test campaign for " \
           "PROTéGé, whose main purpose is " \
           "to ensure that dmclient has decent " \
           "unit tests." == archive_meta.description


class TestInvalid:
    """
    Ensure dmclient can cope with malformed archive data, by exercising open and
    load functions with malformed data and examining the exceptions thrown.
    """

    def test_not_archive(self):
        with pytest.raises(InvalidArchiveError):
            archive.open("resources/test/notarchive.dmc")

    def test_corrupt_metadata(self):
        with pytest.raises(InvalidArchiveMetadataError):
            archive.open("resources/test/badmeta.dmc")


def test_export(archive_meta, tmpdir):
    src = tmpdir.mkdir("src")
    f = src.join("foo.txt")
    f.write("hello, world")

    bar = src.mkdir("bar")
    f = bar.join("bar.txt")
    f.write("goodbye, world")

    dest = tmpdir.mkdir("dest")
    tfpath = dest.join("foo.dml")
    archive.export(archive_meta, str(src), tfpath)

    with tarfile.open(tfpath, "r:bz2") as tf:
        members = [ti.name for ti in tf.getmembers()]
        assert 4 == len(members)
        assert "foo.txt" in members
        assert "properties.json" in members
        assert "bar" in members and tf.getmember("bar").isdir()
        assert "bar/bar.txt" in members

        with open("resources/test/protege/testcampaign/properties.json") as f:
            schema = ArchiveMetaSchema()
            m1, errors = schema.loads(f.read())
            assert not errors
            m2, errors = schema.loads(
                tf.extractfile("properties.json").read().decode())
            assert not errors
            # Hacky way of determining if equal and unmolested.
            test_loading_metadata(m1)
            test_loading_metadata(m2)
