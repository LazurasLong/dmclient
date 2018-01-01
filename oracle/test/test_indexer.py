import pytest

from oracle.index import Indexer


@pytest.fixture
def indexer():
    return Indexer()


@pytest.fixture
def indexed_document(indexer, provider, note):
    doc, _ = indexer.index_note(provider, note)
    return doc


def test_document_data(indexed_document):
    assert indexed_document.get_data().decode() == "foo bar baz"


def test_term_list(indexed_document):
    termlist = {term.term.decode() for term in indexed_document.termlist()}
    # Why the 'Z's?
    assert termlist == {'foo', 'bar', 'baz', 'Zfoo', 'Zbar', 'Zbaz'}
