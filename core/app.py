import os
from logging import getLogger
from random import randint

from PyQt5.QtCore import QTimer, pyqtSlot, QRunnable, QThreadPool, QThread, \
    QObject

import core.config
import game.config
from campaign import Campaign
from campaign.controller import CampaignController
from core import archive, filters, generate_uuid
from core.archive import PropertiesSchema, InvalidArchiveError, open_archive, \
    ArchiveMeta
from game import GameSystem
from model.qt import SchemaTableModel
from ui import display_error, get_open_filename, LoadingWindow
from ui.campaign import NewCampaignDialog

log = getLogger(__name__)


class ExistingLibraryError(Exception):
    def __init__(self, path, game_system_id):
        self.path = path
        self.game_system_id = game_system_id


class GameSystemManager:
    def __init__(self):
        self.systems = SchemaTableModel(PropertiesSchema, GameSystem,
                                        readonly=True)
        self._last_path = {}

    def add_gamesystem(self, archive_meta):
        """Register a game system on the filesystem.

        :param archive:
        :raises: ExistingLibraryError if the game system ID is already registered
        """
        path = archive_meta.last_seen_path
        game_system_id = archive_meta.game_system_id
        if game_system_id in [game_system.id for game_system in self.systems]:
            raise ExistingLibraryError(path, game_system_id)
        game_system = GameSystem(0, archive_meta.name)
        self.systems.append(game_system)
        self._last_path[game_system.id] = path

    def load_config(self, config_path):
        game_systems = []
        last_seen_at = {}
        with open(config_path) as config_file:
            reader = game.config.reader(config_file)
            for id, path in reader:
                try:
                    meta = ArchiveMeta.load(path)
                    self.add_gamesystem(meta)
                # bleh
                except (
                OSError, InvalidArchiveError, ExistingLibraryError) as e:
                    log.warning("game system `%s' (at `%s') is invalid: %s", id,
                                path, e)

        return game_systems, last_seen_at

    def save_config(self, config_path):
        with open(config_path, 'w') as config_file:
            writer = game.config.writer(config_file)
            for system in self.systems:
                path = self._last_path[system.id]
                writer.write_system(system, path)


class LoadCampaignTask(QRunnable):
    """
    This is sort of like a future, in that it has a ``result``.
    """

    def __init__(self, path, cb, done_cb):
        super().__init__()
        self.meta = path
        self.cb = cb
        self.done_cb = done_cb
        self.result = "foo"

    @pyqtSlot()
    def run(self):
        try:
            self.result = "/:memory:"
            self.done_cb()
            return

            meta = open_archive(path)

            campaign = load_campaign(path)
            self.on_campaign_loaded(campaign)
            core.config.appconfig().last_campaign_path = path
        except (OSError, InvalidArchiveError) as e:
            log.error("Cannot load campaign: %s", error.exception)

    @staticmethod
    def temp_path(campaign_id):
        return os.path.join(TEMP_DIR, campaign_id)


class AppController(QObject):
    game_config_path = os.path.join(core.config.CONFIG_PATH, "gamesystems")

    def __init__(self, qapp, delphi):
        """

        :param qapp: A ``QApplication`` instance (avoids global var shenanigans)
        :param delphi:
        """
        super().__init__(qapp)
        self.qapp = qapp
        self.delphi = delphi
        self.campaign_controller = None
        self.thread_pool = QThreadPool()
        self.games = GameSystemManager()
        self.main_window = None
        try:
            self.games.load_config(self.game_config_path)
        except FileNotFoundError:
            pass

    def show_new_campaign(self):
        assert self.main_window is None
        w = self.main_window = NewCampaignDialog(self.games.systems, {})
        w.accepted.connect(self.on_new_campaign)
        w.newGameSystemRequested.triggered.connect(self.on_add_gamesystem)
        w.show()
        w.raise_()

    def on_add_gamesystem(self):
        path = get_open_filename(self.main_window,
                                 "Import game archive", filter_=filters.library,
                                 recent_key="import_game_archive")
        if not path:
            return
        try:
            with archive.open_library(path) as ar:
                self.games.add_gamesystem(ar)
        except (OSError, InvalidArchiveError) as e:
            log.error("failed to load game system: %s", e)
            display_error(self.new_campaign_dialog,
                          "The archive file could not be read.")
        except ExistingLibraryError as e:
            # FIXME this error message is trash
            display_error(self.new_campaign_dialog,
                          "Cannot add duplicate game system with id `{}'".format(
                              e.game_system_id))

    def on_new_campaign(self):
        options = self.main_window.options
        cid = generate_uuid()
        campaign = Campaign(cid)
        self._init_cc(campaign)

    def load_campaign(self, path):
        assert self.main_window is None
        self.main_window = LoadingWindow(loading_text="Loading campaign...")
        task = LoadCampaignTask(path, self.main_window.update_progress,
                                self._on_campaign_loaded)
        self.main_window.set_task(task)
        self.main_window.raise_()
        self.main_window.show()
        self.thread_pool.start(task)

    def _on_campaign_loaded(self):
        QTimer.singleShot(0, self.on_campaign_loaded)

    @pyqtSlot()
    def on_campaign_loaded(self):
        campaign_path = self.main_window.task.result
        if not campaign_path:
            display_error(self.main_window, "The campaign could not be loaded.")
            self.show_new_campaign()
            return
        self.main_window.hide()
        self.main_window.destroy()
        self.main_window = None

        campaign = self._create_campaign(campaign_path)
        self._init_cc(campaign)

    def _create_campaign(self, campaign_path):
        return Campaign(0)

    def _init_cc(self, campaign):
        controller = CampaignController(campaign, self.delphi)
        window = controller.view
        window.show()
        window.raise_()
        window.quit.triggered.connect(self.qapp.quit)
        self.main_window = window

    def shutdown(self):
        try:
            self.games.save_config(self.game_config_path)
        except OSError as e:
            log.error("failed to save gamesystem config: %s", e)
