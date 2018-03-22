from datetime import datetime


def feature(name):
    pass


class Module:
    def __init__(self, author, license, creation_date):
        self.assets = []
        self.author = author
        self.license = license
        self.creation_date = creation_date


class GameSystem:
    def __init__(self, id, name, author, description, creation_date, revision_date):
        self.id = id
        self.name = name
        self.author = author
        self.description = description
        self.creation_date = creation_date
        self.revision_date = revision_date
        self.dice = []
        self.modules = []

    def __hash__(self):
        return hash(self.id)

    @classmethod
    def default(cls):
        return GameSystem("GAME", "", " ", " ", datetime.now(), datetime.now())
