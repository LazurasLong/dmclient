"""Index a variety of plaintext formats, including:

1. Plaintext
2. Rich-text
3. Markdown
4. Others?!
5. The "custom monster format" alex has developed for his campaigns  :)

"""
from oracle.provider import FileProvider


class Provider(FileProvider):
    def __init__(self):
        pass

    def index_file_metadata(self, path):
        pass

    def extract_file_text(self, path):
        with open(path) as f:
            return f.readlines()

