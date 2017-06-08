# model/schema.py
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

"""Schemas (powered by marshmallow) determine:

1. How JSON files in archives are parsed, producing domain objects
2. How views map to the domain objects (see ``ui.schemamap``)

Because of the second reason above, it is required that all schemas are ordered.

"""

from marshmallow import Schema as MarshmallowSchema, post_load, fields


class Schema(MarshmallowSchema):
    class Meta:
        ordered = True


class PropertiesSchema(Schema):
    id = fields.UUID(required=True)
    name = fields.Str(default="")
    description = fields.Str(default="")
    creation_date = fields.DateTime(format="iso")


class ArchivePropertiesSchema(PropertiesSchema):
    author = fields.Str(default="")
    game_system_id = fields.Str(required=True)
    revision_date = fields.DateTime(format="iso")


class CampaignPropertiesSchema(ArchivePropertiesSchema):
    pass


class LibraryPropertiesSchema(ArchivePropertiesSchema):
    pass


class SessionPropertiesSchema(Schema):
    start_time = fields.DateTime(required=True, format="iso")
    end_time = fields.DateTime(required=False, format="iso")
    attendees = fields.List(fields.UUID(), required=False)


class XYCoordSchema(Schema):
    x = fields.Float()
    y = fields.Float()

    @post_load
    def make_coord(self, data):
        return data["x"], data["y"]
