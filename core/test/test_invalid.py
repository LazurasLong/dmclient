
"""Ensure dmclient can cope with malformed data."""
import pytest

from core.archive import InvalidArchiveError, load_campaign


def test_bad_archives():
    with pytest.raises(InvalidArchiveError):
        load_campaign("resources/test/notarchive.dmc")
    with pytest.raises(InvalidArchiveError):
        load_campaign("resources/test/badarchive.dmc")


def test_bad_session_data():
    campaign = load_campaign("resources/test/badsessiondata.dmc")
    assert len(campaign.sessions) == 1
