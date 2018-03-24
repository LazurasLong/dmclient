# core/app.py
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

import os
import shutil
from datetime import datetime
from logging import getLogger

from PyQt5.QtCore import QTimer, pyqtSlot, QRunnable, QThreadPool, QObject

import core.config
import game.config
from campaign import Campaign
from campaign.controller import CampaignController
from core import filters, generate_uuid, archive
from core.archive import PropertiesSchema, InvalidArchiveError, ArchiveMeta
from core.async import mtexec
from core.controller import QtController
from game import GameSystem
from model.qt import SchemaTableModel
from oracle import DummyDelphi, Delphi
from ui import display_error, get_open_filename, LoadingDialog, \
    get_polar_response, get_trial_response, TrialResponses
from ui.campaign import NewCampaignDialog
from ui.game.system import SystemPropertiesEditor, SystemIDValidator

log = getLogger(__name__)


class ExistingLibraryError(Exception):
    def __init__(self, path, game_system_id):
        self.path = path
        self.game_system_id = game_system_id


class GameSystemController(QtController):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.systems = SchemaTableModel(PropertiesSchema, GameSystem,
                                        readonly=True)
        self.cc = None
        self.view = None
        self._last_path = {}

    def bind(self, view):
        self.view = view

    def add_from_archive(self, archive_meta):
        """
        Register a game system on the filesystem.

        :param archive_meta:
        :raises: ExistingLibraryError if the game system ID is already
        registered
        """
        path = archive_meta.last_seen_path
        game_system_id = archive_meta.game_system_id
        if game_system_id in [game_system.id for game_system in self.systems]:
            raise ExistingLibraryError(path, game_system_id)
        game_system = GameSystem(game_system_id,
                                 archive_meta.name,
                                 archive_meta.author,
                                 archive_meta.description,
                                 archive_meta.creation_date,
                                 archive_meta.revision_date)
        self.add(game_system)
        self._last_path[game_system.id] = path

    def add(self, game_system):
        self.systems.append(game_system)

    def load_config(self, config_path):
        game_systems = []
        last_seen_at = {}
        with open(config_path) as config_file:
            reader = game.config.reader(config_file)
            for id_, path in reader:
                try:
                    meta = ArchiveMeta.load(path)
                    self.add_from_archive(meta)
                # bleh
                except (OSError, InvalidArchiveError,
                        ExistingLibraryError) as e:
                    log.warning("game system `%s' (at `%s') is invalid: %s",
                                id_, path, e)

        return game_systems, last_seen_at

    def save_config(self, config_path):
        with open(config_path, 'w') as config_file:
            writer = game.config.writer(config_file)
            for system in self.systems:
                try:
                    path = self._last_path[system.id]
                except KeyError:
                    # That's ok, just means we haven't yet saved this. Skip.
                    pass
                else:
                    writer.write_system(system, path)

    def get(self, id_):
        """
        Return the game system associated with ``id``, or raise ``KeyError`` if
        the id is not associated with a game system.
        """
        # ugh
        for system in self.systems:
            if system.id == id_:
                return system
        raise KeyError

    def has_unsaved(self):
        return True

    @pyqtSlot()
    def on_game_system_properties(self):
        if self.cc:
            game_system = self.cc.campaign.game_system
        else:
            # FIXME
            game_system = GameSystem.default()
        validator = SystemIDValidator(self.systems)
        dlg = SystemPropertiesEditor(game_system,
                                     validator)
        dlg.accepted.connect(lambda: self.on_game_system_update(dlg))
        dlg.show()

    @pyqtSlot()
    def on_game_system_update(self, propdlg):
        game_system = propdlg.game_system
        self.systems.append(game_system)

    @pyqtSlot()
    def on_add_gamesystem(self):
        path = get_open_filename(self.view, "Import game archive",
                                 filter_=filters.library,
                                 recent_key="import_game_archive")
        if not path:
            return
        try:
            meta = archive.open(path)
            self.add_from_archive(meta)
            self.view.enable_create()
        except (OSError, InvalidArchiveError) as e:
            log.error("failed to load game system: %s", e)
            display_error(self.view,
                          "The archive file could not be read.")
        except ExistingLibraryError as e:
            display_error(self.view,
                          "Cannot add duplicate game system with id `{}'".format(
                              e.game_system_id))


class LoadCampaignTask(QRunnable):
    """
    This is sort of like a future, in that it has a ``result``.
    """

    def __init__(self, archive_path, cb, done_cb):
        super().__init__()
        self.archive_path = archive_path
        self.cb = cb
        self.done_cb = done_cb
        self.result = None
        self.exception = None

    @pyqtSlot()
    def run(self):
        try:
            self.cb(5)
            meta = archive.open(self.archive_path)
            self.cb(15)
            destination = CampaignController.extracted_archive_path(meta)
            archive.unpack(meta, destination)
            self.cb(80)
            self.result = meta, destination
        except Exception as e:
            self.exception = e
        else:
            core.config.appconfig().last_campaign_path = self.archive_path
        self.done_cb()


def shutdown_method(f):
    """
    A decorator that offers a safety harness: if the function ``f`` throws
    ``OSError``, the exception is caught and logged but further operations in
    the pipeline are not stopped as a result.

    Note: I tried making this a part of ``AppController`` because it's the only
    place where this is currently used. It works, but PyCharm gets very upset.
    """

    def wrapped(self, *args):
        try:
            f(self, *args)
        except OSError as e:
            log.exception("failed to shutdown: %s", e)

    return wrapped


class AppController(QObject):
    game_config_path = os.path.join(core.config.CONFIG_PATH, "gamesystems")

    def __init__(self, args, qapp, oracle_zygote):
        """

        :param qapp: A ``QApplication`` instance (avoids global var shenanigans)
        :param delphi:
        """
        super().__init__(qapp)
        self.args = args
        self.qapp = qapp
        self.oracle_zygote = oracle_zygote
        self.cc = None
        self.thread_pool = QThreadPool()
        self.game_controller = GameSystemController()
        self.main_window = None
        try:
            self.game_controller.load_config(self.game_config_path)
        except FileNotFoundError:
            pass

    def show_new_campaign(self):
        g = self.game_controller
        w = self.main_window = NewCampaignDialog(g.systems, {})
        g.bind(w)
        w.accepted.connect(self.on_new_campaign)
        w.loadExistingCampaignRequested.connect(self.on_open_campaign)
        w.importGameSystem.triggered.connect(g.on_add_gamesystem)
        w.newGameSystem.triggered.connect(g.on_game_system_properties)
        w.show()
        w.raise_()

    @pyqtSlot()
    def on_new_campaign(self):
        """
        Called by the ``File`` menu or when the new campaign dialog is accepted.
        """
        options = self.main_window.options
        self._clear_main_window()

        cid = generate_uuid()
        game_system = self.game_controller.get(options["game_system"])
        campaign = Campaign(cid, game_system)
        for attr in ["name", "author"]:
            option = options[attr]
            if option:
                setattr(campaign, attr, option)
        os.mkdir(CampaignController.working_directory(campaign))
        os.mkdir(CampaignController.extracted_archive_path(campaign))
        self._init_cc(campaign)

    @pyqtSlot()
    def on_open_campaign(self):
        """
        Called by the ``File`` menu and by the new campaign dialog's
        *open existing* button.
        """
        path = get_open_filename(self.main_window, "Open campaign",
                                 filter_=filters.campaign)
        if not path:
            return
        if self.cc:
            self.cc.shutdown()
        self._clear_main_window()
        self.load_campaign(path)

    def load_campaign(self, path):
        assert self.main_window is None
        self.main_window = LoadingDialog(loading_text="Loading campaign...")
        task = LoadCampaignTask(path, mtexec(self.main_window.update_progress),
                                self._on_campaign_loaded)
        self.main_window.set_task(task)
        self.main_window.raise_()
        self.main_window.show()
        QTimer.singleShot(0, lambda: self.thread_pool.start(task))

    def _on_campaign_loaded(self):
        QTimer.singleShot(0, self.on_campaign_loaded)

    @pyqtSlot()
    def on_campaign_loaded(self):
        result = self.main_window.task.result
        if not result:
            log.exception("failed to load campaign: %s",
                          self.main_window.task.exception)
            display_error(self.main_window, "The campaign could not be loaded.")
            self._clear_main_window()
            self.show_new_campaign()
            return
        meta, campaign_path = result
        self._clear_main_window()
        campaign = self._create_campaign(meta)
        self._init_cc(campaign, meta)

    def _clear_main_window(self):
        self.main_window.hide()
        self.main_window.destroy()
        self.main_window = None

    def _create_campaign(self, meta):
        game_system = self.game_controller.get(meta.game_system_id)
        campaign = Campaign(meta.id, game_system)
        campaign.name = meta.name
        campaign.author = meta.author
        campaign.creation_date = meta.creation_date
        campaign.revision_date = datetime.now()
        return campaign

    def _init_cc(self, campaign, archive_meta=None):
        assert self.main_window is None
        if self.args.disable_oracle:
            delphi = DummyDelphi()
        else:
            delphi = Delphi(self.oracle_zygote, self.delphi_quit)

        # TODO: Ensure that the previous campaign was flushed out (i.e., tmp)
        cc = self.cc = CampaignController(delphi, campaign, archive_meta)

        self.game_controller.cc = cc

        window = self.main_window = cc.view
        window.check_for_updates.triggered.connect(self.on_check_updates)
        window.game_system_properties.triggered.connect(
            self.game_controller.on_game_system_properties)
        window.open_campaign.triggered.connect(self.on_open_campaign)
        window.quit.triggered.connect(self.on_quit_requested)
        window.closeRequested.connect(self.on_quit_requested_event)

        delphi.start(CampaignController.database_path(campaign),
                     CampaignController.xapian_database_path(campaign),
                     cc.search_controller)

        window.show()
        window.raise_()

    def on_quit_requested(self):
        if self.game_controller.has_unsaved():
            res = get_trial_response(self.main_window,
                                     "There are unsaved game system changes.\n"
                                     "\n"
                                     "Do you want to save these changes to disc?",
                                     "Save...", title="Unsaved game systems")
            if res == TrialResponses.dissenting:
                return False
            elif res == TrialResponses.default:
                print("here is where I would export unused archives")
        self.qapp.quit()
        return True

    def on_quit_requested_event(self, event):
        if not self.on_quit_requested():
            event.ignore()
            return
        event.accept()

    def shutdown(self):
        """
        Perform shutdown tasks. It is assumed at this point that save states
        have been validated and ensured, because at this point the ship is
        being doused with kerosine and there's nothing that can stop it  :)
        """
        self._raze_delphi()
        self._flush_game_config()
        self._clear_campaign_temp_files()

    @shutdown_method
    def _raze_delphi(self):
        # FIXME this is a dumpster fire
        if self.cc:
            self.cc.delphi.shutdown()
        self.oracle_zygote.kill()

    @shutdown_method
    def _flush_game_config(self):
        self.game_controller.save_config(self.game_config_path)

    @shutdown_method
    def _clear_campaign_temp_files(self):
        if self.cc:
            shutil.rmtree(self.cc.working_directory(self.cc.campaign))

    @pyqtSlot()
    def on_check_updates(self):
        dlg = LoadingDialog(self.main_window,
                            loading_text="Checking for updates...")
        dlg.raise_()
        dlg.show()

    def delphi_quit(self, code):
        if code == 0:
            # SIGTERM, it's time to go.
            self.qapp.quit()
