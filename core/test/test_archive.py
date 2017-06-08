"""Tests for the campaign archive structure."""

import os.path

import pytest
from PyQt5.QtCore import QDateTime
from dateutil.parser import parse as dtparse

from core.archive import load_campaign, Archive, NoSuchArchiveFileError, \
    NoSuchDirectoryError


@pytest.fixture(scope="module")
def archive():
    archive_ = None
    try:
        archive_ = Archive.open("resources/test/protege/testcampaign.dmc")
        yield archive_
    finally:
        if archive_:
            archive_.close()


def test_file_named(archive):
    # looks for thrown exception I guess
    assert archive.file("properties.json") is not None

    file_ = archive.file("testfile")
    assert file_.read() == b"This file is for archive tests and is " \
                           b"not otherwise part of the campaign.\n"

    with pytest.raises(NoSuchArchiveFileError):
        archive.file("DOES_NOT_EXIST")


def test_textfile_named(archive):
    textfile = archive.textfile("testfile")
    assert textfile.read() == "This file is for archive tests and " \
                              "is not otherwise part of the campaign.\n"

    with pytest.raises(NoSuchArchiveFileError):
        archive.textfile("DOES_NOT_EXIST")


def test_directories(archive):
    dir_ = archive.subdir("sessions")
    subdirs = list(dir_.dirs())
    assert len(subdirs) == 2, "there should be two session dirs present!"

    subdir = dir_.subdir("4")
    file_ = subdir.textfile("properties.json")
    assert file_.read().strip() == '{\n\t"start_time": "2016-04-21"\n}'

    with pytest.raises(NoSuchDirectoryError):
        archive.subdir("DOES_NOT_EXIST")


def test_subdir_files(archive):
    dir_ = archive.subdir(os.path.join("sessions", "0"))
    files = list(dir_.files())
    assert len(files) == 2
    filenames = [file.name for file in files]
    assert "properties.json" in filenames
    assert "session.log" in filenames


@pytest.fixture
def campaign():
    # FIXME: must be generated manually!
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
    assert session.start_time == QDateTime(dtparse("2016-04-20").date())
    assert len(session.notes) == 0  # FIXME

    session = campaign.sessions[1]
    assert session.start_time == QDateTime(dtparse("2016-04-21").date())
    assert len(session.notes) == 0
    assert session.log == "This is what happened in the session!\n"


def test_maps(campaign):
    assert len(campaign.maps) == 1

    map = campaign.maps[0]
    # assert map["background"] == "dirt.png"
    # assert map["mask"] == "map_mask.png"
    # assert len(map["pins"]) == 5
