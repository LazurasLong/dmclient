from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class DescribableMixin:
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)

    def __init__(self, name, description):
        self.name = name
        self.description = description


class DateMixin:
    creation_date = Column(DateTime)
    modified_date = Column(DateTime)

    def __init__(self, creation, modification):
        self.creation_date = creation
        self.modification_date = modification


class AssetMixin(DescribableMixin, DateMixin):  # TODO better name
    pass
