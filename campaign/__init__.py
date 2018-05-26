# campaign/__init__.py
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

from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, String

from model import CampaignBase, DescribableMixin


class Player(CampaignBase, DescribableMixin):
    __tablename__ = "player"

    kills = Column(Integer)


class CampaignSession(CampaignBase, DescribableMixin):
    __tablename__ = "session"

    start_time = Column(DateTime)
    end_time = Column(DateTime)
    log = Column(String)

    # notes, attendees

    def __str__(self):
        return str(self.start_time)


class Campaign:
    """
    Because campaigns consist of data that extent far beyond the database,
    ``Campaign``s are not implemented using SQL, instead as plain-old Python
    instances.
    """
    def __init__(self, id, game_system):
        self.id = id
        self.game_system = game_system
        self.name = "Untitled campaign"
        self.author = "Unknown"
        self.description = ""
        self.dice = game_system.dice
        self.creation_date = datetime.now()
        self.revision_date = datetime.now()
        self.players = {}
        self.documents = []
        self.encounters = []
        self.regional_maps = {}
        self.encounter_maps = {}
