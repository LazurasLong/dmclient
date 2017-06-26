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
    def is_acceptable_document(self, path):
        """
        Most provider subclasses will check the path and use ``magic`` module.

        :param path:
        :return:  ``True`` if the document can be indexed by this provider,
                  ``False`` otherwise.
        """
        return True

    def extract_document_text(self, path):  # wtf is path
        try:
            return self.extract_file_text(path)
        except OSError as e:
            raise IndexError("failed to index document!") from e

    def extract_file_text(self, path):
        raise NotImplementedError
