# campaign/__init__.py
# Copyright (C) 2017 Alex Mair. All rights reserved.
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


class Campaign:
    def __init__(self, id,
                 name="Untitled campaign",
                 author="",
                 game_system_id=None,
                 description="",
                 creation_date=None,
                 revision_date=None):
        self.id = id
        self.name = name
        self.author = author
        self.game_system_id = game_system_id
        self.description = description
        self.creation_date = creation_date
        self.revision_date = revision_date
        self.players = {}
        self.sessions = []
        self.documents = []
        self.encounters = []
        self.regional_maps = {}
        self.encounter_maps = {}
        self.notes = []


class CampaignSession:
    def __init__(self, timestamp=None, log=""):
        if timestamp is None:
            timestamp = datetime.now()
        self.start_time = timestamp
        self.end_time = timestamp
        self.log = log
        self.attendees = set()
        self.notes = {}
        self.recording = None

    def __str__(self):
        return str(self.start_time)


class Note:
    def __init__(self, id):
        self.id = id


class ExternalNote(Note):
    def __init__(self, id, url):
        super().__init__(id)
        self.url = url
