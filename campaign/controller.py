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

from PyQt5.QtCore import QTimer, pyqtSlot
from PyQt5.QtGui import QIcon

from model.tree import Node, DictNode, ListNode, NodeFactory, TreeModel
from ui.battlemap.controls import ControlScheme
from ui.battlemap.widgets import RegionalMapView
from ui.campaign import CampaignWindow

log = getLogger(__name__)


class SearchController:
    def __init__(self, delphi, interval_msec=250):
        delphi.search_callback = self.search_results_updated
        self._delphi = delphi
        self._update_delay = interval_msec
        self.search_query = ""
        self._timer = QTimer()
        self._timer.setInterval(interval_msec)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.search_requested)

    @property
    def update_delay(self):
        return self._update_delay

    @update_delay.setter
    def update_delay(self, delay):
        self._update_delay = delay
        self._timer.setInterval(delay)

    def search_text_changed(self, text):
        log.debug("search text changed: {}".format(text))
        self.search_query = text
        if not text:
            return
        self._timer.start()

    def search_requested(self):
        self._timer.stop()
        log.debug("a search was requested: `%s'", self.search_query)
        self._delphi.send_search_query(self.search_query)

    def search_results_updated(self, results):
        log.debug("SearchController received search results!")
        for section in results:
            for result in results[section]:
                log.debug("received a result: %s:%s", section, result)


class CampaignController:
    def __init__(self, campaign, delphi):
        self.campaign = campaign
        self.delphi = delphi
        self.search_controller = SearchController(delphi)
        self.view = None

    def show_map(self, id):
        log.debug("show_map(%s)", id)
        try:
            map = self.campaign.regional_maps[id]
            map_view = RegionalMapView(map, ControlScheme(), self.view)
            self.view.tab_controller.make_tab(map_view, map.name)
            self.view.addToolBar(map_view.toolbar)
        except KeyError as e:
            log.error("cannot open map %s: %s", id, e)

    def show_session(self):
        raise NotImplementedError

    def spawn_view(self, parent=None):
        v = self.view = CampaignWindow(self.campaign)

        # FIXME this should not be here.
        asset_tree = self.build_asset_tree(self.campaign)
        model = TreeModel(asset_tree)

        v.assetTree.setModel(model)
        v.assetTree.doubleClicked.connect(model.actionTriggered)

        sc = self.search_controller
        v.searchEdit.textChanged.connect(sc.search_text_changed)
        v.searchEdit.returnPressed.connect(sc.search_requested)

        return v

    def build_asset_tree(self, campaign):
        """

        :return: A Node for the asset tree.
        """
        map_node_factory = NodeFactory(action=self.show_map)

        region = DictNode(text="Regional", child_factory=map_node_factory)
        region.apply(campaign.regional_maps)
        encounter = DictNode(text="Encounters", child_factory=map_node_factory)
        encounter.apply(campaign.encounter_maps)

        map_node = Node(icon=QIcon(":/icons/maps.png"), text="Maps")
        map_node.add_child(region)
        map_node.add_child(encounter)

        icon = QIcon(":/icons/sessions.png")
        session_node_factory = NodeFactory(action=self.show_session, icon=icon)
        session_node = ListNode(icon=icon, text="Sessions",
                                child_factory=session_node_factory)

        player_node = ListNode(text="players", icon=QIcon(":/icons/party.png"))

        search_node = ListNode(icon=QIcon(":/icons/books.png"),
                               text="Documents")
        search_node.apply(self.delphi.documents)

        root = Node()
        root.add_children([map_node, session_node, player_node, search_node])
        return root
