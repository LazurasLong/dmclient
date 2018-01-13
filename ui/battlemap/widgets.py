# ui/battlemap/widgets.py
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

"""

.. todo::
    Something like apply_control_scheme() which switches the *Event methods?
"""

from functools import partial
from logging import getLogger

from PyQt5.QtCore import QItemSelection, QItemSelectionModel, QModelIndex, \
    QPointF, Qt, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QWheelEvent
from PyQt5.QtWidgets import *

from campaign.battlemap import MapLayerSchema, ViewMode
from core import hrlowername
from core.math import clamp, previous_multiple
from ui.actions import AbortedAction
from ui.battlemap.tools import MapActionManager, maptool, RoadActionManager, \
    GeographicActionManager, FailureMode
from ui.schemamap import schema_ui_map
from ui.widgets.battlemap_inspector import Ui_BattlemapInspector
from ui.widgets.map_layer_properties import Ui_MapLayerPropertiesDialog

log = getLogger(__name__)


class PoliticalActionManager(MapActionManager):
    @maptool(icon="magnifying_glass")
    def inspect(self, entity):
        return self.controller.make_properties_dialog(entity)

    @maptool(name="Spawn/Destroy Entity", icon="castle",
             view_modes=(ViewMode.political, ViewMode.geographic))
    def entity_manipulation(self, point):
        entity = self.map.entity_at(point)
        if entity:
            self.delegate.set_selected_entity(entity)
        else:
            self.map.spawn_entity(point)


class RegionalMapView(QGraphicsView):
    def __init__(self, battlemap, control_scheme, parent=None):
        QGraphicsView.__init__(self, parent)
        self.map = battlemap
        self.control_scheme = control_scheme
        self.is_grid_visible = False
        self.view_mode = ViewMode.geographic
        self.selected_tool = None
        self.contract_args = []
        self.action_managers = {cls.__name__: cls(self.map, self)
                                for cls in (RoadActionManager,
                                            GeographicActionManager,
                                            PoliticalActionManager,
                                            )}

        self.toolbar = QToolBar()

        group = self._view_group = QActionGroup(self)
        for mode in ViewMode:
            action = QAction(QIcon(":/icons/{}.png".format(mode.name)),
                             "Show {} view".format(hrlowername(mode.name)),
                             self)
            action.triggered.connect(partial(self.set_view_mode, mode))
            group.addAction(action)
            self.toolbar.addAction(action)
        group.actions()[0].setChecked(True)
        self.toolbar.addSeparator()

        for manager in self.action_managers.values():
            for action in manager.action_group(self).actions():
                self.toolbar.addAction(action)
            self.toolbar.addSeparator()  # FIXME separator always on the end
        action = QAction(QIcon(":/icons/grid.png"), "Toggle grid overlay",
                         parent)
        action.setCheckable(True)
        action.toggled.connect(self.toggle_grid_visible)
        self.toolbar.addAction(action)

        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setScene(battlemap.scene)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

    @property
    def control_scheme(self):
        return self._control_scheme

    @control_scheme.setter
    def control_scheme(self, control_scheme):
        self._control_scheme = control_scheme
        self.setTransformationAnchor(control_scheme.view_anchor)

    def make_properties_dialog(self, entity):
        pass

    @pyqtSlot(bool)
    def toggle_grid_visible(self, visible):
        self.is_grid_visible = visible

    @pyqtSlot()
    def set_view_mode(self, view_mode):
        log.debug("View mode changed to %s", view_mode)
        self.view_mode = view_mode  # ugh qt
        self.update()  # FIXME: Doesn't seem to repaint on X11?

    def reset_tool_state(self):
        """Clear any active contract and the selected tool."""
        raise NotImplementedError

    def get_entity(self, event):
        item = self.itemAt(event.pos())
        entity = self.map.entity(item)
        return entity

    def set_selected_entity(self, entity):
        pass

    def get_point(self, event):
        qpoint = self.mapToScene(event.pos())
        log.debug("returning {}".format(qpoint))
        point = qpoint.x(), qpoint.y()
        if not self.map.point_in_bounds(point):
            raise AbortedAction
        return point

    def get_biome(self, event):
        point = self.get_point(event)
        return self.map.biome_at(point)

    def zoom_camera(self, dy):
        # TODO minimum and maximum zoom levels
        # TODO user-configurable scale_factor (or not???)

        dy = clamp(dy, -1.1, 1.1)
        # prevent view from transforming weirdly (i.e. flipping upside down)
        if dy < 0:
            dy = 1 / -dy
        self.scale(dy, dy)

    def drawBackground(self, painter, rect):
        map_w, map_h = self.map.size
        map_palette = self.map.palette
        if rect.x() < 0 or rect.y() < 0 or map_w < rect.width() or map_h < rect.height():
            painter.fillRect(rect, map_palette.void_brush)

        try:
            background = map_palette.backgrounds[self.view_mode]
            painter.drawPixmap(rect, background, rect)
        except KeyError:
            painter.fillRect(rect, Qt.red)

    def drawForeground(self, painter, rect):
        if self.is_grid_visible:
            w, h = self.map.size
            rx, ry = rect.x(), rect.y()
            sx, sy = self.map.scale_factor
            start_x = max(previous_multiple(rx, sx), 0)
            start_y = max(previous_multiple(ry, sy), 0)
            end_x = min(w, int(rx + rect.width()))
            end_y = min(h, int(ry + rect.height()))
            # vertical
            for x in range(start_x, end_x, sx):
                painter.drawLine(QPointF(x, start_y), QPointF(x, end_y))
            # horizontal
            for y in range(start_y, end_y, sy):
                painter.drawLine(QPointF(start_x, y), QPointF(end_x, y))
        super().drawForeground(painter, rect)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            raise NotImplementedError
        super().keyPressEvent(event)

    def mouseMoveEvent(self, event):
        # No debug on this guy. Can you say... noisy?
        # FIXME: We should only selectively turn this on, otherwise... slow?
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        log.debug("MapView::mousePressEvent(%s)", event)

        if not self.selected_tool:
            log.debug("no selected tool, not doing anything")
            return super().mousePressEvent(event)

        tool = self.selected_tool
        assert 0 < len(tool.contract)
        current_requirement = tool.contract[len(self.contract_args)]
        m_name = "get_{}".format(current_requirement)
        m = getattr(self, m_name)  # FIXME this is weird.
        contract_arg = m(event)

        if contract_arg:
            self.contract_args.append(contract_arg)
            log.debug("self.contract_args = %s, tool.contract = %s",
                      self.contract_args, tool.contract)
            if len(self.contract_args) == len(tool.contract):
                tool.activate(*self.contract_args)
                self.contract_args = []
            else:
                log.debug("contract not fulfilled, not activating")
        else:
            # todo: display error?
            log.debug("event %s is not useful for %s", event,
                      self.active_contract)
            failure_mode = tool.failure_mode
            if failure_mode == FailureMode.noop:
                # Nothing to do, the tool figures itself out.
                return
            elif failure_mode == FailureMode.cancel:
                self.reset_tool_state()

    def scrollContentsBy(self, x, y):
        super().scrollContentsBy(x, y)

    def wheelEvent(self, event):
        if self.control_scheme.wheel_zooms:
            dy = event.angleDelta().y()
            # Filter out horizontal wheel motion. We don't support this yet.
            if dy == 0:
                event.ignore()
                return
            self.zoom_camera(dy)
        else:
            if event.modifiers() & Qt.ShiftModifier:
                event = QWheelEvent(event.posF(),
                                    event.globalPosF(),
                                    event.pixelDelta(),
                                    event.angleDelta(),

                                    # Value magically chosen to approximate
                                    # what is happening on nirvana using
                                    # a steelseries mouse...
                                    event.angleDelta().y() / 8,

                                    Qt.Horizontal,  # Qt4 crap
                                    event.buttons(),
                                    event.modifiers(),
                                    event.phase())
            super().wheelEvent(event)


# TODO: Convert to a SchemaTable view.
class BattlemapInspector(QWidget, Ui_BattlemapInspector):
    def __init__(self, parent):  # , map_scene):
        QWidget.__init__(self, parent)
        # self.map_scene = map_scene
        self.current_items = None

        self.setupUi(self)
        self.nameEdit.editingFinished.connect(self.on_name_edit)
        self.browseIconImageButton.setEnabled(False)  # FIXME
        # self.layerComboBox.setModel(self.map_scene.layers)
        self.layerComboBox.currentIndexChanged.connect(self.on_layercb_index)

        self.clear(enabled=False)

    def clear(self, enabled=True):
        for w in [self.nameEdit, self.iconLabel, self.xCoordSpinbox,
                  self.yCoordSpinbox]:
            w.clear()
            w.setEnabled(enabled)
        self.layerComboBox.setEnabled(enabled)
        self.layerComboBox.setCurrentIndex(-1)
        self.additionalPropertiesTable.setModel(None)

    def update(self, items):
        # FIXME: This method is crap; if I change the visibility of a layer..
        # then the inspector gets cleared. Wtf?!
        self.current_items = items

        if len(items) == 0:
            self.clear(enabled=False)
        elif len(items) == 1:
            item = items[0]
            self.clear()
            self.nameEdit.setText(item.name)
            self.iconLabel.setPixmap(item.icon)
            self.layerComboBox.setCurrentIndex(
                    self.map_scene.layers.index_(item.layer))
            self.xCoordSpinbox.setValue(item.pos().x())
            self.yCoordSpinbox.setValue(item.pos().y())
        else:
            self.clear()
            self.nameEdit.setPlaceholderText("%d items" % len(items))
            if all(items[0].layer == item.layer for item in items):
                self.layerComboBox.setCurrentIndex(
                        self.map_scene.layers.index_(items[0].layer))

    def on_name_edit(self):
        if self.current_items:
            for item in self.current_items:
                item.name = self.form.nameEdit.text()

    def on_layercb_index(self, newindex):
        if newindex == -1 or not self.current_items:
            return
        new_layer = self.map_scene.layers[newindex]
        for item in self.current_items:
            new_layer.assign(item)

    def on_selection_change(self):
        items = self.map_scene.selectedItems()
        self.update(items)


class MapLayerPropertiesDialog(QDialog, Ui_MapLayerPropertiesDialog):
    def __init__(self, parent, map):
        QDialog.__init__(self, parent)
        self.map_scene = map
        self.setupUi(self)
        self.browse_icon.setEnabled(False)
        self.mapper = schema_ui_map(MapLayerSchema, map.layers, self)
        self.layers.setModel(self.map_scene.layers)
        self.layers.selectionModel().selectionChanged.connect(
                self.on_layers_selectionChanged)

    def _current_layer(self):
        indexes = self.layers.selectionModel().selectedIndexes()
        assert len(indexes) == 1, "at least default layer should exist!"
        row = indexes[0].row()
        return self.map_scene.layers[row], row

    @pyqtSlot()
    def on_new_layer_clicked(self):
        layers = self.map_scene.layers
        layers.insertRow(1)
        self.layers.selectionModel().select(layers.index(1, 0),
                                            QItemSelectionModel.ClearAndSelect)

    @pyqtSlot()
    def on_delete_layer_clicked(self):
        layers = self.map_scene.layers
        assert 1 < len(layers), "Delete action should be disabled!"
        current, row = self._current_layer()
        new = layers[0]
        for object in current.objects:
            new.assign(object)
        layers.remove(current)
        # FIXME: This was "next_row" but that idea was stupid..
        # Still want a nice refactoring of this though...
        row_to_select = min(layers.rowCount() - 1, row)
        self.layers.selectionModel().select(layers.index(row_to_select, 0),
                                            QItemSelectionModel.ClearAndSelect)

    @pyqtSlot(QItemSelection, QItemSelection)
    def on_layers_selectionChanged(self, selected, deselected):
        indexes = selected.indexes()
        # HACK: We're coming around again anyway so we can afford to do this.
        if not indexes:
            return
        default_selected = self.map_scene.layers.index(0, 0) in indexes
        self.delete_layer.setDisabled(default_selected)
        self.mapper.setCurrentIndex(indexes[0].row())

    @pyqtSlot(QModelIndex)
    def on_showedit(self, index):
        self.show()
        self.mapper.setCurrentIndex(index.row())
        self.layers.setCurrentIndex(index)


class MapLayerPropertiesDock(QDockWidget):
    def __init__(self, layer_model, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Map Layers")
        layer_table = self.layer_table = QTableView(self)
        self.layer_table.setModel(layer_model)
        layer_table.setColumnHidden(2, True)
        layer_table.setColumnHidden(3, True)
        layer_table.resizeColumnsToContents()
        layer_table.verticalHeader().hide()
        header = layer_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.moveSection(0, 1)
        self.setWidget(layer_table)
