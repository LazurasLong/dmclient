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
from game import GameSystem
from model.qt import SchemaTableModel
from oracle import DummyDelphi, Delphi
from ui import display_error, get_open_filename, LoadingDialog
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
        game_system = GameSystem(game_system_id, archive_meta.name)
        self.systems.append(game_system)
        self._last_path[game_system.id] = path

    def load_config(self, config_path):
        game_systems = []
        last_seen_at = {}
        with open(config_path) as config_file:
            reader = game.config.reader(config_file)
            for id_, path in reader:
                try:
                    meta = ArchiveMeta.load(path)
                    self.add_gamesystem(meta)
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
                path = self._last_path[system.id]
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
        self.games = GameSystemManager()
        self.main_window = None
        try:
            self.games.load_config(self.game_config_path)
        except FileNotFoundError:
            pass

    def show_new_campaign(self):
        w = self.main_window = NewCampaignDialog(self.games.systems, {})
        w.accepted.connect(self.on_new_campaign)
        w.loadExistingCampaignRequested.connect(self.on_open_campaign)
        w.newGameSystemRequested.triggered.connect(self.on_add_gamesystem)
        w.show()
        w.raise_()

    def on_add_gamesystem(self):
        path = get_open_filename(self.main_window, "Import game archive",
                                 filter_=filters.library,
                                 recent_key="import_game_archive")
        if not path:
            return
        try:
            meta = archive.open(path)
            self.games.add_gamesystem(meta)
            self.main_window.enable_create()
        except (OSError, InvalidArchiveError) as e:
            log.error("failed to load game system: %s", e)
            display_error(self.main_window,
                          "The archive file could not be read.")
        except ExistingLibraryError as e:
            display_error(self.main_window,
                          "Cannot add duplicate game system with id `{}'".format(
                              e.game_system_id))

    @pyqtSlot()
    def on_new_campaign(self):
        """
        Called by the ``File`` menu or when the new campaign dialog is accepted.
        """
        options = self.main_window.options
        self._clear_main_window()

        cid = generate_uuid()
        game_system = self.games.get(options["game_system"])
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
        game_system = self.games.get(meta.game_system_id)
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
            delphi = Delphi(self.oracle_zygote)

        # TODO: Ensure that the previous campaign was flushed out (i.e., tmp)
        cc = self.cc = CampaignController(delphi, campaign, archive_meta)
        window = cc.view

        window.check_for_updates.triggered.connect(self.on_check_updates)
        window.open_campaign.triggered.connect(self.on_open_campaign)
        window.quit.triggered.connect(self.qapp.quit)

        self.main_window = window
        delphi.start(CampaignController.database_path(campaign),
                     CampaignController.xapian_database_path(campaign),
                     cc.search_controller)

        window.show()
        window.raise_()

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
        self.games.save_config(self.game_config_path)

    @shutdown_method
    def _clear_campaign_temp_files(self):
        if self.cc:
            shutil.rmtree(self.cc.working_directory(self.cc.campaign))

    def on_check_updates(self):
        dlg = LoadingDialog(self.main_window,
                            loading_text="Checking for updates...")
        dlg.raise_()
        dlg.show()
