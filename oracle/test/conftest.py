import pytest
import xapian
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from campaign.note import Note
from model import GameBase
from oracle.oracle import OracleDatabase


class DummyNote(Note):
    def __init__(self):
        self.url = "foo://bar"


@pytest.fixture
def note():
    return DummyNote()


class FooProvider:
    def __init__(self, text):
        self.text = text

    def extract_document_text(self, _url):
        return self.text


@pytest.fixture
def provider():
    return FooProvider("foo bar baz")


@pytest.fixture
def campaign_db(note):
    engine = create_engine("sqlite:///:memory:")
    GameBase.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(note)
    session.commit()
    return engine


@pytest.fixture
def oracle_db(tmpdir):
    xapiandb = xapian.WritableDatabase(str(tmpdir.join("xapian.db")),
                                       xapian.DB_CREATE)
    database = OracleDatabase(xapiandb)
    return database
