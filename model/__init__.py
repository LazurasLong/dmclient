from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

"""
The declarative base class for all tables in the ``game`` namespace.

This pertains primarily to the game system libraries, anything in a .DML file.
"""
GameBase = declarative_base()

"""
The declarative base for all tables in the ``campaign`` namespace.

This includes anything that would be added to the database in a campaign
archive.
"""
CampaignBase = declarative_base()


class DescribableMixin:
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __str__(self):
        return self.name


class DateMixin:
    creation_date = Column(DateTime)
    modified_date = Column(DateTime)

    def __init__(self, creation, modification):
        self.creation_date = creation
        self.modification_date = modification


class AssetMixin(DescribableMixin, DateMixin):  # TODO better name
    """A combination of DescribeableMixin and DateMixin."""
    pass
