# oracle/index.py
# Copyright (C) 2018 Alex Mair. All rights reserved.
# This file is part of dmclient.
#
# dmclient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# dmclient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with dmclient.  If not, see <http://www.gnu.org/licenses/>.
#

"""Classes and functions for indexing search providers."""
from logging import getLogger

import xapian

log = getLogger(__name__)


class Indexer:
    def __init__(self):
        stemmer = xapian.Stem("english")
        self.term_generator = xapian.TermGenerator()
        self.term_generator.set_stemmer(stemmer)
        self.stemmer = stemmer

    def index_note(self, provider, note):
        """

        :param provider:
        :param note:
        :return:  The Xapian document associated with the note.
        """
        text = provider.extract_document_text(note.url)
        document = xapian.Document()
        document.set_data(text)
        self.term_generator.set_document(document)
        self.term_generator.index_text(text)
        return document, note.id
