"""The (probably bulk?) aspect of dmclient's searching.

Provides a means to index PDFs.

"""

import subprocess
from logging import getLogger
from tempfile import NamedTemporaryFile

from core.config import TMP_PATH
from oracle.exceptions import IndexingError
from oracle.provider import FileProvider

log = getLogger(__name__)


def pdf2txt(source_name, destination_file):
    return subprocess.call(["pdf2txt.py", source_name], stdout=destination_file)


class PDFProvider(FileProvider):
    def index_file_contents(self, path):
        with NamedTemporaryFile(prefix="dmoracle_", dir=TMP_PATH) as f:
            log.debug("pdf2txt-ing `%s' to `%s'...", path, f.name)
            ret = pdf2txt(path, f)
            if ret:
                log.error("pdf2txt failed, retcode %d", ret)
                raise IndexingError
            f.seek(0)
            return f.readlines()

