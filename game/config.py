import csv
import os
from logging import getLogger
from uuid import UUID

log = getLogger(__name__)


def reader(configfile):
    _reader = csv.reader(configfile, dialect="unix")
    for row in _reader:
        if 2 < len(row):
            log.warning("line contains extra garbage")
            continue
        try:
            system_id, path = row[0], row[1]
        except IndexError:
            log.warning("line contains not enough garbage...")
            continue
        if not os.path.exists(path):
            log.warning("`%s' no longer exists on the filesystem "
                        "(expected it to be at `%s')",
                        system_id, path)
            continue
        yield UUID(system_id), path


def writer(configfile):
    _writer = csv.writer(configfile, dialect="unix")
    return GameSystemConfigWriter(_writer)


class GameSystemConfigWriter:
    def __init__(self, csvwriter):
        self.csvwriter = csvwriter

    def write_system(self, system, path):
        self.csvwriter.writerow([system.id, path])
