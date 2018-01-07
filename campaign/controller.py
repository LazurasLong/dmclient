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

import os
from logging import getLogger

from PyQt5.QtCore import QObject, QTimer, pyqtSlot, QPoint
from PyQt5.QtGui import QIcon, QStandardItem
from PyQt5.QtWidgets import QMenu
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from campaign import Player
from campaign.note import ExternalNote, Note, InternalNote
from core import filters, archive
from core.config import TMP_PATH
from model import GameBase
from model.tree import FixedNode, TableNode, TreeModel, BadNode
from ui import get_open_filename, display_error, get_save_filename, \
    display_warning
from ui.battlemap.controls import ControlScheme
from ui.battlemap.widgets import RegionalMapView
from ui.campaign import CampaignPropertiesDialog, CampaignWindow
from ui.note import NoteEditorDialog
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
    def __init__(self, cc):
        self._cc = cc
        view = cc.view
        super().__init__(view)
        self.view = view  # ?!
        self.tree_node = TableNode(cc.db(), Note,
                                   icon=QIcon(":/icons/books.png"),
                                   text="Documents", delegate=self,
                                   item_action=self.item_doubleclicked)
        view.import_document.triggered.connect(self.on_import_document)
        view.add_document.triggered.connect(self.on_add_document)
        view.remove_document.triggered.connect(self.on_remove_document)

    def item_doubleclicked(self, node):
        # FIXME this is incrensely hacky.
        db = self._cc.db()
        try:
            item = db.query(InternalNote).filter(Note.id == node.id)[0]
            dlg = NoteEditorDialog(item, db, self.view)
            dlg.raise_()
            dlg.exec()
        except IndexError:
            # It's an external note.
            pass

    def context_menu(self):
        window = self.view
        return [window.import_document, window.add_document,
                window.remove_document]

    def item_context_menu(self):
        raise NotImplementedError

    @pyqtSlot()
    def on_new_document(self):
        base_note = Note(name="Untitled", author=self._cc.campaign.author)
        internal_note = InternalNote(note_id=base_note.id,
                                     text="New note...")
        db = self._cc.db()
        db.add(base_note)
        db.add(internal_note)
        db.commit()
        self.tree_node.update()

    @pyqtSlot()
    def on_import_document(self):
        path = get_open_filename(self.view, "Import text document", filters.txt)
        if not path:
            return
        try:
            with open(path) as f:
                contents = f.read()
        except OSError as e:
            log.error("failed to import note: %s", e)
            display_error(self.view, "The document could not be imported.",
                          "Unable to import document")
        else:
            base_note = Note(name=os.path.basename(path),
                             author=self._cc.campaign.author)
            note = InternalNote(text=contents)
            db = self._cc.db()
            db.add(base_note)
            db.add(note)
            db.commit()
            self.tree_node.update()

    @pyqtSlot()
    def on_add_document(self):
        path = get_open_filename(self.view, "Add external document",
                                 filters.document)
        if not path:
            return
        try:
            with open(path):
                pass
            base_note = Note(name=os.path.basename(path),
                             author="")
            note = ExternalNote(note_id=base_note.id, url=path)
            db = self._cc.db()
            db.add(base_note)
            db.add(note)
            db.commit()
            self.tree_node.update()
        except OSError as e:
            log.error("could not open note: %s", e)

    @pyqtSlot()
    def on_remove_document(self):
        raise NotImplementedError


class MapController(QObject):
    def __init__(self, cc):
        view = cc.view
        super().__init__(view)
        self.campaign_window = view
        self.tree_node = FixedNode(icon=QIcon(":/icons/maps.png"), text="Maps",
                                   action=self.show_map)
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


class PlayerController(QObject):
    def __init__(self, cc):
        view = cc.view
        super().__init__(view)
        self.tree_node = TableNode(cc.db(), Player, text="Players",
                                   icon=QIcon(":/icons/party.png"))


class SessionController(QObject):
    def __init__(self, cc):
        view = cc.view
        super().__init__(view)
        icon = QIcon(":/icons/sessions.png")
        self.tree_node = BadNode(text="Campaign sessions")
        # self.tree_node = TableNode(CampaignSession,
        #                            cc.db(), icon=icon, text="Sessions")

    def show_session(self):
        pass


class CampaignController(QObject):
    """
    A ``CampaignController`` is the controller for a campaign during the
    lifetime of an application. To keep this class small, it is mostly
    responsible for managing the highest level logic on a campaign and
    delegating operations to sub-controllers.

    ``CampaignController`` instances operate on already existing campaigns. The
    creation of, for example, the working directory for the campaign is expected
    to be handled externally, e.g. by the ``AppController`` or test harnesses.
    """

    def __init__(self, delphi, campaign, archive_meta=None):
        super().__init__(None)
        self.delphi = delphi
        self.campaign = campaign
        self.archive_meta = archive_meta

        self.dirty = True

        campaign_db_path = self.database_path(campaign)
        self._engine = create_engine("sqlite:///{}".format(campaign_db_path), echo=True)
        self._Session = sessionmaker(bind=self._engine)
        GameBase.metadata.create_all(self._engine)

        self.view = CampaignWindow(self.campaign)
        self.map_controller = None
        self.player_controller = None
        self.session_controller = None
        self.search_controller = None
        self._init_subcontrollers()

        asset_tree = self.build_asset_tree(self.campaign)
        self.asset_tree_model = TreeModel(asset_tree)

        self._init_view()

    def db(self):
        """
        :return: A session to the database.
        """
        self._Session.configure(bind=self._engine)
        return self._Session()

    @staticmethod
    def working_directory(campaign):
        """
        Return an absolute path to the working directory for the campaign,
        usually ``TEMP_DIR/{campaign.id}/``.
        """
        return os.path.join(TMP_PATH, str(campaign.id))

    @staticmethod
    def extracted_archive_path(campaign):
        return os.path.join(CampaignController.working_directory(campaign),
                            "archive")

    @staticmethod
    def database_path(campaign):
        return os.path.join(CampaignController.extracted_archive_path(campaign),
                            "campaign.db")

    @staticmethod
    def build_context_menu(listing, name):
        context_menu = QMenu(name)
        for action in listing:
            context_menu.addAction(action)
        return context_menu

    @staticmethod
    def xapian_database_path(campaign):
        return os.path.join(CampaignController.working_directory(campaign),
                            "oracle")

    def _init_subcontrollers(self):
        self.map_controller = MapController(self)
        self.player_controller = PlayerController(self)
        self.note_controller = NoteController(self)
        self.session_controller = SessionController(self)

        self.search_controller = SearchController(self.delphi,
                                                  SearchCompleter())

    def _init_view(self):
        sc = self.search_controller
        v = self.view

        v.save_campaign.triggered.connect(self.on_sync_campaign)
        v.save_campaign_as.triggered.connect(self.on_save_campaign_as)

        v.searchEdit.textChanged.connect(sc.on_search_text_changed)
        v.searchEdit.returnPressed.connect(sc.on_search_requested)

        v.assetTree.setModel(self.asset_tree_model)
        v.assetTree.doubleClicked.connect(self.asset_tree_doubleclick)
        v.assetTree.customContextMenuRequested.connect(self.asset_tree_context_menu_requested)

        v.campaign_properties.triggered.connect(self.on_campaign_properties)

    def build_asset_tree(self, campaign):
        root = FixedNode(*[controller.tree_node for controller in
                           [self.map_controller, self.session_controller,
                            self.player_controller, self.note_controller]])
        return root

    def window_moved(self):
        """Called when the main campaign window is moved."""
        self.search_controller.update_results_popup()

    def asset_tree_doubleclick(self, index):
        node = index.internalPointer()
        if node.action:
            node.action(node)
        elif node.parent and node.parent.item_action:
            node.parent.item_action(node)

    @pyqtSlot(QPoint)
    def asset_tree_context_menu_requested(self, point):
        index = self.view.assetTree.indexAt(point)
        node = index.internalPointer()
        controller = node.delegate
        if not controller:
            log.debug("There is no controller on this node.")
            return
        context_menu = CampaignController.build_context_menu(
            controller.context_menu(),
            "Asset tree context menu")
        context_menu.exec(controller.view.mapToGlobal(point))

    @pyqtSlot()
    def on_sync_campaign(self):
        am = self.archive_meta
        if not am:
            self._save_campaign_as()
            return
        if am.last_seen_path and not os.path.exists(am.last_seen_path):
            display_warning(self.view, "The campaign archive appears to have "
                                       "been moved or deleted.\n\nPlease "
                                       "select a new location to save this "
                                       "archive.")
            am.last_seen_path = self._save_campaign_as()
            return
        raise NotImplementedError

    @pyqtSlot()
    def on_save_campaign_as(self):
        # Do not update the "last seen" path,
        # this is presumably for making a copy.
        self._save_campaign_as()

    @pyqtSlot()
    def on_campaign_properties(self):
        dlg = CampaignPropertiesDialog(self.campaign, self.view)
        dlg.accepted.connect(self.on_properties_update(dlg))
        dlg.show()

    @pyqtSlot()
    def on_properties_update(self, propdlg):
        options = propdlg.options
        for k, v in options.items():
            setattr(self.campaign, k, v)
        self.view.setWindowTitle(self.campaign.name)
        self.properties_dialog = None

    def _save_campaign_as(self):
        path = get_save_filename(self.view, "Save campaign as",
                                 filter_=filters.campaign)
        if not path:
            return
        try:
            archive.export(self.archive_meta,
                           CampaignController.extracted_archive_path(self.campaign),
                           path)
        except OSError as e:
            log.error("could not export campaign: %s", e)
        else:
            return path

