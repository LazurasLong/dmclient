# campaign/battlemap.py
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
from collections import defaultdict
from enum import Enum
from logging import getLogger

from PyQt5.QtCore import QPoint, QPointF, QRect, QSize, Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QPixmap, QRegion, QTransform
from PyQt5.QtWidgets import *
from marshmallow import fields, post_load
from pygraph.classes.graph import graph

from model.qt import SchemaTableModel
from model.schema import Schema, XYCoordSchema

log = getLogger(__name__)

default_palette_spec = (
    ((0, 0, 255), "ocean_base.jpg"),
    ((0, 187, 255), "freshwater.png"),
    ((255, 255, 102), "beach.png"),
    ((187, 187, 0), "prairie.png"),
    ((0, 187, 0), "grassland.png"),
    ((102, 187, 102), "swamp.png"),
    ((0, 102, 0), "forest.png"),
    ((187, 102, 102), "hills.png"),
    ((255, 0, 255), "mountains.png"),
)


class MapError(Exception):
    pass


class ViewMode(Enum):
    geographic = 1
    political = 2
    road_network = 3


def default_palette():
    """Creates the default ``MapPalette`` object with all of the normal boring
    dmclient defaults.

    """
    palette = MapPalette(default_palette_spec)
    palette.void_brush = Qt.gray
    palette.dummy_icon = QPixmap(":/icons/dummy.png")
    palette.default_icon = QPixmap(":/battlemap/map_pin.png")\
        .scaled(32, 32, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    return palette


class MapPalette:
    def __init__(self, palette_spec):
        self._palette = {}
        self.default_icon = None
        self.dummy_icon = None
        self.void_brush = Qt.darkGray
        for colour, image_name in palette_spec:
            pixmap = QPixmap(":/battlemap/{}".format(image_name))
            self._palette[colour] = pixmap
        self.backgrounds = {}
        self.icon_set = defaultdict(lambda: self.dummy_icon)

    def __iter__(self):
        return iter(self._palette.items())

    def render_mask(self, mask):
        size = QSize(mask.width(), mask.height())
        rect = QRect(QPoint(0, 0), size)
        pixmap = QPixmap(size)
        painter = QPainter(pixmap)
        for mask_colour, texture_pixmap in self._palette.items():
            qcolour = QColor(*mask_colour)
            mask_bitmap = mask.createMaskFromColor(qcolour, Qt.MaskOutColor)
            mask_region = QRegion(mask_bitmap)
            painter.setClipRegion(mask_region)
            painter.drawTiledPixmap(rect, texture_pixmap)
        return pixmap

    def render_background(self, name, mask):
        self.backgrounds[name] = self.render_mask(mask)


class MapEntity(QGraphicsItemGroup):
    """A generic map entity."""
    def __init__(self, name, position, icon=None):
        QGraphicsItemGroup.__init__(self)

        self._name = name
        self.icon = icon
        self.layer = None  # FIXME?

        self.setFlags(self.flags()
                      & ~QGraphicsItem.ItemIsMovable
                      | QGraphicsItem.ItemIsSelectable)
        if icon:
            graphic = QGraphicsPixmapItem(icon)
            bb = graphic.boundingRect()
            graphic.setPos(-bb.width() / 2, -bb.height())
            self.addToGroup(graphic)

        font = QFont("Courier New")
        font.setPointSize(8)
        text = self.text = QGraphicsSimpleTextItem(name)
        text.setFont(font)
        text.setBrush(Qt.white)
        text.setPos(-text.boundingRect().width() / 2, 10)
        self.addToGroup(text)

        self.setPos(*position)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        self.text.setText(value)
        self.text.setPos(-self.text.boundingRect().width() / 2, 10)  # FIXME

    def mousePressEvent(self, event):
        print("hey, you poked me")


class LabelledMapEntity(MapEntity):
    pass


class MapLayer:
    """Objects (entries?) currently have a 1:1 relationship to layers.

    Layers steal ownership of objects from each other. Not sure if that's
    a bad thing...

    """
    def __init__(self, name="Untitled layer", visible=True, z=0, default_icon=None):
        self.name = name
        self.objects = []
        self._visible = visible
        self.z = z
        self.default_icon = default_icon

    def __str__(self):
        return "MapLayer(%s, %d)" % (self.name, self.z)

    def assign(self, entry):  # TODO: better name
        if entry.layer:
            entry.layer.objects.remove(entry)
        entry.layer = self
        self.objects.append(entry)

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, visible=True):
        self._visible = visible
        for o in self.objects:
            o.setVisible(visible)


class MapLayers(SchemaTableModel):
    def __init__(self, parent=None):
        SchemaTableModel.__init__(self, MapLayerSchema, MapLayer, parent)
        pixmap = QPixmap(":/icons/eye-icon.png")
        assert pixmap.width() > 1 and pixmap.height() > 1
        self.setHeaderData(0, Qt.Horizontal, "")
        self.setHeaderData(1, Qt.Horizontal, "")
        self.setHeaderData(1, Qt.Horizontal, pixmap, Qt.DecorationRole)


class Map:
    def __init__(self, biome_mask, political_mask, palette, name="Untitled map",
                 scale_factor=(16, 16)):
        self.biome_mask = biome_mask
        self.size = biome_mask.width(), biome_mask.height()
        self.palette = palette
        self.palette.render_background(ViewMode.geographic, biome_mask)
        self.palette.render_background(ViewMode.political, biome_mask)
        self.name = name
        self.scale_factor = scale_factor

        self.entities = set()
        self.layers = [MapLayer("Default Layer")]
        self.road_network = graph()

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, *self.size)

    def __str__(self):
        return self.name

    def fill_from_jsondict(self, dict_):
        self.add_pins(dict_["pins"])

    def spawn_entity(self, point, name="New Entity"):
        pixmap = QPixmap(":/icons/castle.png")
        entry = MapEntity(name, point, pixmap)
        self.scene.addItem(entry)
        return entry

    def add_pins(self, locations, texture=None, layer=0):
        try:
            _layer = self.layers[layer]
        except IndexError:
            log.warning("layer %d does not exist; adding to default.", layer)
            _layer = self.layers[0]
        for name, position in locations:
            entry = self.spawn_entity(position, name)
            _layer.assign(entry)

    def biome_at(self, point):
        pass

    def entity_at(self, point):
        x, y = point
        qpoint = QPointF(x, y)
        return self.scene.itemAt(qpoint, QTransform())

    def entity(self, graphics_item):
        """Return the associated ``MapEntity`` for a given graphics item."""
        try:
            pass
        except KeyError as e:
            log.error("invalid graphics item? %s", graphics_item)
            return None

    def point_in_bounds(self, point):
        return (0, 0) < point <= self.size


class MapPinSchema(Schema):
    name = fields.Str()
    location = fields.Nested(XYCoordSchema)

    @post_load
    def make_pin(self, data):
        return data["name"], data["location"]


class MapLayerSchema(Schema):
    name = fields.Str()
    visible = fields.Bool(default=True)
    z = fields.Float()
    default_icon = fields.Str()


class MapSchema(Schema):
    name = fields.Str()
    background = fields.Str()
    mask = fields.Str()
    pins = fields.Nested(MapPinSchema, many=True)

