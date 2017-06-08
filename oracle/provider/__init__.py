
"""A *search provider* provides the oracle with a source of documents.

Some examples::

1. Certain components within dmclient
1. The filesystem
1. External cloud services (e.g. Google Drive)

It's a bit weird, since some providers exist within the main dmclient process.
This is to gain access to the Python objects directly. It was faster to
implement but might cause issues? Other providers (such as the PDF and
Google Drive) exist in the oracle process.

"""


class SearchProvider:
    def __init__(self):
        pass


class FileProvider(SearchProvider):
    def index_document(self, path):  # wtf is path
        try:
            return self.index_file_contents(path)
        except OSError as e:
            raise IndexError("failed to index document!") from e

    def index_file_contents(self, path):
        raise NotImplementedError

