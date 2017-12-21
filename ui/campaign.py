# ui/campaign.py
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

"""Qt-specific main campaign window and some supporting dialogs."""

import webbrowser
from logging import getLogger

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *

from campaign import Campaign, CampaignSession
from campaign.battlemap import Map
from core import filters
from core.archive import InvalidArchiveError
from core.config import APP_NAME, BUG_URL, DONATE_URL
from model.qt import SchemaTableModel
from model.schema import SessionPropertiesSchema
from ui import display_error, get_open_filename, ResourceDialogManager, \
    spacer_widget
from ui.about import show as show_about
from ui.archive import ArchiveDialog
from ui.preferences import show_preferences
from ui.tools import DiceController as DiceController, DiceRollerDialog, QObject
from ui.widgets.campaign.new import Ui_NewCampaignDialog
from ui.widgets.campaign.properties import Ui_CampaignProperties
from ui.widgets.campaign.session import Ui_CampaignSession
from ui.widgets.campaign.window import Ui_MainWindow

log = getLogger(__name__)


class CampaignWindow(QMainWindow, Ui_MainWindow):
    windowMoved = pyqtSignal()
    windowResized = pyqtSignal()

    def __init__(self, campaign):
        QMainWindow.__init__(self)
        self.setupUi(self)
        self.remove_document.setIcon(QIcon.fromTheme("edit-delete"))
        self.statusbar.showMessage("Welcome to %s" % APP_NAME)
        self.setWindowTitle(campaign.name)

        self._init_dialogs(campaign)
        self.tab_controller = TabController(self.tabWidget)
        self._init_asset_tree()
        self._init_session_list(campaign)
        self._init_map_components()
        self._init_search_widgets()

        # FIXME this seems to do a subprocess thing. We don't want their stderr!
        self.digitalbusking.triggered.connect(lambda: webbrowser.open(DONATE_URL))
        self.complain.triggered.connect(
            lambda: webbrowser.open(BUG_URL))
        self.about.triggered.connect(show_about)

    def _init_dialogs(self, campaign):
        self._campaign_properties = CampaignPropertiesDialog(campaign, self)
        self.campaign_properties.triggered.connect(
            self._campaign_properties.show)
        # self._campaign_properties.accepted.connect(self.on_properties_change)

    def _init_asset_tree(self):
        self.assetTree = QTreeView()
        self.assetTree.setContextMenuPolicy(Qt.CustomContextMenu)

        dock = QDockWidget(self)
        dock.setWindowTitle("Campaign assets")
        dock.setWidget(self.assetTree)

        self.showhide_assettree.triggered.connect(dock.setVisible)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    def _init_search_widgets(self):
        tb = self.toolBar
        edit = self.searchEdit = QLineEdit(self)

        edit.setPlaceholderText("Search")
        self.search_oracle.triggered.connect(
            lambda: edit.setFocus(Qt.TabFocusReason))
        tb.addWidget(spacer_widget())
        tb.addWidget(edit)

        def hacky_stopper(*args):
            log.error("Should not add widgets to the toolbar now!")

        tb.addWidget = hacky_stopper

    def _init_session_list(self, campaign):
        dock = QDockWidget(self)
        self.sessionList = QListView(dock)

        self.sessionList.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.sessionList.addAction(self.new_session)

        dock.setWidget(self.sessionList)
        dock.setWindowTitle("Sessions")
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        session_model = SchemaTableModel(SessionPropertiesSchema,
                                         CampaignSession,
                                         data=campaign.sessions)
        session_model.readonly = True
        self.sessionList.setModel(session_model)
        self.sessionListManager = ResourceDialogManager(session_model, CampaignSessionDialog, self)
        self.sessionList.doubleClicked.connect(self.sessionListManager.on_show)

    def _init_map_components(self):
        dock = QDockWidget(self)
        dock.setWindowTitle("Map Inspector")
        action = self.showhide_inspector
        action.setChecked(True)
        action.triggered.connect(dock.setVisible)
        dock.visibilityChanged.connect(action.setChecked)

        # inspector = self.map_inspector = BattlemapInspector(dock)
        #
        # dock.setWidget(inspector)
        # self.addDockWidget(Qt.RightDockWidgetArea, dock)
        #
        # dock = MapLayerPropertiesDock(self.map_scene.layers, self)
        # dock.layer_table.doubleClicked.connect(self._map_layers_dlg.on_showedit)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    @pyqtSlot()
    def on_import_rules_triggered(self):
        path = get_open_filename(self, "Open Archive",
                                 filters.join(filters.library,
                                              filters.expansion))
        if path == "":
            return
        try:
            dlg = ArchiveDialog(self, path)
            dlg.exec()
            raise NotImplementedError
        except InvalidArchiveError as e:
            log.error("could not open archive: %s" % e.__cause__)
            display_error(self, "The archive file is corrupted or malformed.")
        except OSError as e:
            log.error(e)
            display_error(self, "The archive could not be read.")

    @pyqtSlot()
    def on_edit_preferences_triggered(self):
        show_preferences(parent=self)

    #
    # Tools menu
    #

    @pyqtSlot()
    def on_roller_triggered(self):
        standard_array = [20, 12, 10, 8, 6, 4, 100]
        controller = DiceController(standard_array)
        roller = DiceRollerDialog(controller)
        roller.show()
        roller.raise_()

    @pyqtSlot(Campaign)
    def on_properties_change(self, campaign):
        self.setWindowTitle(campaign.name)

    @pyqtSlot(Map)
    def on_map_selection_changed(self, map):
        """Whenever a tab with a map is opened,
        update the various components.

        """
        inspector = self.map_inspector
        inspector.xCoordSpinbox.setRange(0, self.map_scene.width())
        inspector.yCoordSpinbox.setRange(0, self.map_scene.height())
        map.scene.selectionChanged.connect(inspector.on_selection_change)


class TabPageWrapper(QObject):
    tabChangeRequested = pyqtSignal()
    accepted = pyqtSignal()

    def __init__(self, widget, tab_controller, parent=None):
        super().__init__(parent)
        self.widget = widget
        self.tab_controller = tab_controller

    def show(self):
        self.tab_controller.switch_to_tab(self)


class TabController(QObject):
    def __init__(self, tab_widget, parent=None):
        super().__init__(parent)
        assert tab_widget.count() == 1, "expected tab laid out in Designer!"
        bar = tab_widget.tabBar()
        bar.setTabButton(0, QTabBar.RightSide, None)
        tab_widget.tabCloseRequested.connect(self.on_tab_close_requested)
        tab_widget.currentChanged.connect(self.on_current_tab_changed)

        self._tabs = [None]  # Dirty hack.
        self.tab_widget = tab_widget

    def make_tab(self, widget, name):
        tab = TabPageWrapper(widget, self)
        self._tabs.append(tab)
        self.tab_widget.addTab(widget, name)
        return tab

    def on_tab_close_requested(self, tab_index):
        if tab_index == 0:
            log.error("cannot close the first tab!")
            return
        self.tab_widget.removeTab(tab_index)
        self._tabs[tab_index].accepted.emit()
        del self._tabs[tab_index]

    def switch_to_tab(self, tab):
        self.tab_widget.setCurrentWidget(tab.widget)

    def on_current_tab_changed(self, index):
        log.debug("current tab was changed to %d", index)

    @pyqtSlot()
    def on_campaign_load(self):
        stacked = self.tab_widget.widget(0).findChildren(QStackedWidget)
        assert len(stacked) == 1
        stacked[0].setCurrentIndex(1)


class NewCampaignDialog(QDialog, Ui_NewCampaignDialog):
    def __init__(self, game_systems, options):
        QDialog.__init__(self)
        self.setupUi(self)
        button = self.bb.button(QDialogButtonBox.Ok)
        button.setText("Create campaign!")
        button.setIcon(QIcon(":/icons/logo.png"))
        self.game_systems.setSelectionMode(QAbstractItemView.SingleSelection)
        self.game_systems.setModel(game_systems)
        self.game_systems.setModelColumn(1)
        self.game_systems.addAction(self.newGameSystemRequested)
        self.game_systems.setCurrentIndex(game_systems.index(0, 1))
        self._options = options

    @property
    def options(self):
        options = self._options
        options["name"] = self.campaign_name.text()
        options["author"] = self.author_name.text()
        options["game_system"] = self._get_selected_gamesystem_id()
        return options

    def _get_selected_gamesystem_id(self):
        model = self.game_systems.model()
        selected = self.game_systems.selectedIndexes()[0].row()
        game_system_id = model.data(model.index(selected, 0))
        return game_system_id


class CampaignPropertiesDialog(QDialog, Ui_CampaignProperties):
    """
    Unfortunately, this dialog is modal due to some lazily imposed restrictions.
    """

    def __init__(self, campaign, parent):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setModal(True)
        self.removeSelectedModules.setEnabled(False)

        # self.model = SchemaTableModel(CampaignPropertiesSchema, Campaign,
        #                               data=[campaign])
        # self.mapper = schema_ui_map(CampaignPropertiesSchema, self.model, self)

        self.setWindowTitle("%s properties" % campaign.name)


class CampaignSessionDialog(QDialog, Ui_CampaignSession):
    def __init__(self, session, parent):
        QDialog.__init__(self, parent)
        self.setupUi(self)

