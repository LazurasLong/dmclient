from queue import Queue
from threading import Thread

import xapian


class Searcher:
    def __init__(self, stemmer):
        self.query_parser = xapian.QueryParser()
        self.query_parser.set_stemmer(stemmer)
        self.query_parser.set_stemming_strategy(xapian.QueryParser.STEM_SOME)
        self.thread = Thread(target=self.run, name="searcher")
        self.pending = Queue()
        self.database = None

    def database_changed(self, database):
        # FIXME this is going to cause a race condition if the db changes
        # whilst we are searching for something......
        self.database = database
        self.query_parser.set_database(database.xdb)

    def run(self):
        while 1:
            query = self.pending.get()
            with self.database.lock:
                self.print_results(query)

    def print_results(self, query):
        enquire = xapian.Enquire(self.database.xdb)
        query = self.query_parser.parse_query(query)
        enquire.set_query(query)
        matches = enquire.get_mset(0, 10)
        print("%d results found" % matches.get_matches_estimated())
        for m in matches:
            print("\t{}: {}%% docid={}\n\t\t{}".format(m.rank, m.percent,
                                                       m.docid,
                                                       m.document.get_data()))
