import pytest

from campaign.note import Note


@pytest.fixture
def note():
    return Note(url="ftp://foo/bar/")


def test_type(note):
    assert note.type == "ftp"
