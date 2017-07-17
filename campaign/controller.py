# campaign/controller.py
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

from logging import getLogger

from PyQt5.QtCore import QObject, QTimer, pyqtSlot
from PyQt5.QtGui import QIcon, QStandardItem
from PyQt5.QtWidgets import QMenu

from core import filters
from model.tree import DictNode, ListNode, Node, NodeFactory, TreeModel
from ui import get_open_filename
from ui.battlemap.controls import ControlScheme
from ui.battlemap.widgets import RegionalMapView
from ui.campaign import CampaignWindow
from ui.search import SearchCompleter

log = getLogger(__name__)


class SearchController(QObject):
    """
    .. todo::
        Make this class more MVC-ish. It does too much. It'd be nice if it also
        followed the general pattern of ``spawn_view()``.

    """
    def __init__(self, delphi, completer, interval_msec=250):
        super().__init__()
        self._delphi = delphi
        delphi.responder = self

        self._update_delay = interval_msec
        self.search_query = ""

        self._timer = QTimer()
        self._timer.setInterval(interval_msec)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.on_search_requested)

    @property
    def update_delay(self):
        return self._update_delay

    @update_delay.setter
    def update_delay(self, delay):
        self._update_delay = delay
        self._timer.setInterval(delay)

    @property
    def results_visible(self):
        return self.results_popup.visible()

    @results_visible.setter
    def results_visible(self, visible):
        if visible:
            self.update_results_popup()
            self.results_popup.show()
        else:
            self.results_popup.hide()

    def parent_moved(self):
        self.update_results_popup()

    def parent_resized(self):
        self.update_results_popup()

    def set_blurb_visible(self, visible=True):
        if visible:
            self.results_popup.indexing_blurb.show()
        else:
            self.results_popup.indexing_blurb.hide()

    def update_results_popup(self):
        geo = self.lineedit.geometry()
        parent = self.lineedit.parentWidget()
        geo.moveTopLeft(parent.mapToGlobal(geo.topLeft()))
        geo.setY(geo.y() + geo.height())
        self.results_popup.setGeometry(geo)
        self.results_popup.show()
        self.results_popup.raise_()

    @pyqtSlot(str)
    def on_search_text_changed(self, text):
        log.debug("search text changed: {}".format(text))
        self.search_query = text
        if not text:
            return
        self._timer.start()

    @pyqtSlot()
    def on_search_requested(self):
        if not self._delphi.enabled:
            log.error("A search was requested but the oracle is not available.")
            return
        log.debug("a search was requested: `%s'", self.search_query)
        self._timer.stop()
        self._delphi.search_query(self.search_query)

    @pyqtSlot()
    def on_search_results_updated(self, results):
        log.debug("SearchController received search results!")
        model = self._build_results_model(results)
        self.results_popup.setModel(model)

    def set_search_results(self, results):
        model = self.model
        for section in results:
            section_item = QStandardItem(section)
            section_item.setEditable(False)
            section_item.setSelectable(False)
            for name, icon in results[section]:
                item = QStandardItem(name)
                item.setIcon(icon)
                item.setEditable(False)
                section_item.appendRow(item)
            model.appendRow(section_item)


class NoteController(QObject):
    def __init__(self, campaign_window):
        """

        :param campaign_window:  Ugh, because Qt is weird. And all of the
        QActions are defined there. Some refactoring is probably needed.
        """
        super().__init__(campaign_window)
        self.campaign_window = campaign_window
        self.tree_node = ListNode(icon=QIcon(":/icons/books.png"),
                                  text="Documents")
        campaign_window.import_document.triggered.connect(self.on_import_document)
        campaign_window.add_external_document.triggered.connect(self.on_add_external_document)
        campaign_window.remove_document.triggered.connect(self.on_remove_document)
        # search_node.apply(self.delphi.documents)

    def context_menu(self):
        window = self.campaign_window
        return [window.import_document,
                window.add_external_document,
                window.remove_document]

    def item_context_menu(self):
        raise NotImplementedError

    @pyqtSlot()
    def on_import_document(self):
        path = get_open_filename(self.view, "Add external document",
                                 filters.document)
        if not path:
            return
        try:
            raise NotImplementedError
        except OSError as e:
            log.error("could not open note: %s", e)

    @pyqtSlot()
    def on_add_external_document(self):
        raise NotImplementedError

    @pyqtSlot()
    def on_remove_document(self):
        raise NotImplementedError


class MapController:
    def __init__(self, campaign_window):
        self.campaign_window = campaign_window
        map_node_factory = NodeFactory(action=self.show_map)

        region = DictNode(text="Regional", child_factory=map_node_factory)
        # region.apply(campaign.regional_maps)
        encounter = DictNode(text="Encounters", child_factory=map_node_factory)
        # encounter.apply(campaign.encounter_maps)

        self.tree_node = Node(icon=QIcon(":/icons/maps.png"), text="Maps")
        self.tree_node.add_child(region)
        self.tree_node.add_child(encounter)

        self.toolbar = None

    def show_map(self, node):
        id = node.id
        log.debug("show_map(%s)", id)
        try:
            map = self.campaign.regional_maps[id]
            self.campaign_window.tab_controller.make_tab(map.id, map.name)
        except KeyError as e:
            log.error("cannot open map %s: %s", id, e)

    def spawn_view(self):
        # called by tab controller if need be
        return RegionalMapView(map, ControlScheme(), self.campaign_window)


class PlayerController:
    def __init__(self, view):
        self.tree_node = ListNode(text="Players", icon=QIcon(":/icons/party.png"),
                                  delegate=self)


class SessionController:
    def __init__(self, view):
        icon = QIcon(":/icons/sessions.png")
        session_node_factory = NodeFactory(action=self.show_session, icon=icon)
        self.tree_node = ListNode(icon=icon, text="Sessions",
                                  child_factory=session_node_factory)

    def show_session(self):
        pass


class CampaignController:
    def __init__(self, campaign, delphi):
        self.campaign = campaign
        self.delphi = delphi

        # FIXME this does not belong here...
        self.delphi.init_database(campaign.id)

        self.view = CampaignWindow(self.campaign)
        # blah blah pycharm
        self.map_controller = \
            self.player_controller = \
            self.session_controller = \
            self.search_controller = None
        self._init_subcontrollers(self.view)

        asset_tree = self.build_asset_tree(self.campaign)
        model = self.asset_tree_model = TreeModel(asset_tree)

        at = self.view.assetTree
        at.setModel(model)
        at.doubleClicked.connect(self.asset_tree_doubleclick)
        at.customContextMenuRequested.connect(self.asset_tree_context_menu_requested)

    def _init_subcontrollers(self, view):
        self.map_controller = MapController(view)
        self.player_controller = PlayerController(view)
        self.note_controller = NoteController(view)
        self.session_controller = SessionController(view)

        self.search_controller = SearchController(self.delphi,
                                                  SearchCompleter())
        sc = self.search_controller  # gross scan/readability, fixme
        view.searchEdit.textChanged.connect(sc.on_search_text_changed)
        view.searchEdit.returnPressed.connect(sc.on_search_requested)

    def build_asset_tree(self, campaign):
        root = Node()
        root.add_children([controller.tree_node
                           for controller in
                           [self.map_controller,
                            self.session_controller,
                            self.player_controller,
                            self.note_controller]])
        return root

    def window_moved(self):
        """Called when the main campaign window is moved."""
        self.search_controller.update_results_popup()

    def asset_tree_doubleclick(self, index):
        log.debug("asset_tree_doubleclick(%s)", index)
        if not index.isValid():
            return
        node = index.internalPointer()
        if node.action:
            node.action(node)  # woo weird!

    def asset_tree_context_menu_requested(self, point):
        log.debug("asset_tree_context_menu_requested(%s)" % point)
        index = self.view.assetTree.indexAt(point)
        node = index.internalPointer()
        controller = node.delegate
        context_menu = QMenu("Asset tree context menu")
        for action in controller.context_menu():
            context_menu.addAction(action)
        context_menu.exec(self.view.mapToGlobal(point))
