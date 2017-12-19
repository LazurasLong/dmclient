"""Tests for the campaign archive structure."""

import pytest
from dateutil.parser import parse as dtparse

from core.archive import *


@pytest.fixture(scope="module")
def archive_meta():
    return ArchiveMeta.load("resources/test/protege/testcampaign.dmc")


def test_loading_metadata(archive_meta):
    assert archive_meta.game_system_id == "PROTEGE"
    assert archive_meta.name == "PROTéGé Test Campaign"
    assert archive_meta.description == "This is a test campaign for " \
                                       "PROTéGé, whose main purpose is " \
                                       "to ensure that dmclient has decent " \
                                       "unit tests."
    assert archive_meta.author == "Alex Mair"
    assert archive_meta.creation_date == dtparse("2016-04-20")
    assert archive_meta.revision_date == dtparse("2016-04-21")


class TestInvalid:
    """
    Ensure dmclient can cope with malformed archive data, by exercising open and
    load functions with malformed data and examining the exceptions thrown.
    """

    def test_not_archive(self):
        with pytest.raises(InvalidArchiveError):
            open_archive("resources/test/notarchive.dmc")

    def test_corrupt_metadata(self):
        with pytest.raises(InvalidArchiveMetadataError):
            open_archive("resources/test/badmeta.dmc")
