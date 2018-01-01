"""
A *search provider* provides the oracle with a source of documents. Providers
are composite objects, which models their source, format, and internal
structure accordingly.

Some examples of the file formats that different users might have include:

- Certain components within dmclient, such as character sheets.
- A plain-text file on a local filesystem, formatted according to
  *reStructuredText*.
- A plain-text file on a cloud service formatted in Markdown.
- External cloud services (e.g. Google Drive's native document format)

Documents can reference other documents in dmclient using a special URL
format, beginning with ``dmc://`` and then the identifier of the document.
This can be copied from dmclient or inserted using its (eventual) rich text
editor.

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
