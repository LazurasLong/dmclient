"""Tests for the campaign archive structure."""

import pytest
from dateutil.parser import parse as dtparse

from core.archive import load_campaign


@pytest.fixture
def campaign():
    return load_campaign("resources/test/protege/testcampaign.dmc")


def test_loading_metadata(campaign):
    assert campaign.name == "PROTéGé Test Campaign"
    assert campaign.author == "Alex Mair"
    assert campaign.game_system_id == "PROTEGE"
    assert campaign.description == "This is a test campaign for PROTéGé, " \
                                   "whose main purpose is to ensure that " \
                                   "dmclient has decent unit tests."


def test_sessions(campaign):
    assert len(campaign.sessions) == 2

    session = campaign.sessions[0]
    assert session.start_time == dtparse("2016-04-20")
    assert len(session.notes) == 0

    session = campaign.sessions[1]
    assert session.start_time == dtparse("2016-04-21")
    assert len(session.notes) == 0
    assert session.log == "This is what happened in the session!\n"

