def feature(name):
    pass


class Module:
    def __init__(self, author, license, creation_date):
        self.assets = []
        self.author = author
        self.license = license
        self.creation_date = creation_date


class GameSystem:
    def __init__(self, id, name, **kwargs):
        self.id = id
        self.name = name
        self.modules = []

    def __hash__(self):
        return hash(self.id)
