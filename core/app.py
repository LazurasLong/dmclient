import os
from logging import getLogger

import core.config
import game.config
from campaign import Campaign
from campaign.controller import CampaignController, SearchController
from core import archive
from core import filters
from core.archive import load_campaign, PropertiesSchema, InvalidArchiveError
from game import GameSystem
from model.qt import SchemaTableModel
from ui.campaign import NewCampaignDialog
from ui import display_error, get_open_filename

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

    def add_gamesystem(self, archive):
        """Register a game system on the filesystem.

        :param archive:
        :raises: ExistingLibraryError if the game system ID is already registered
        """
        path = archive.path
        properties = archive.properties
        game_system_id = properties["game_system_id"]
        if game_system_id in [game_system.id for game_system in self.systems]:
            raise ExistingLibraryError(path, game_system_id)
        game_system = GameSystem(**properties)
        self.systems.append(game_system)
        self._last_path[game_system.id] = path

    @classmethod
    def config_file(cls, mode='r'):
        """Test hook and partial readability."""
        config_path = os.path.join(core.config.CONFIG_PATH, "gamesystems")
        return open(config_path, mode)

    def load_config(self):
        game_systems = []
        last_seen_at = {}
        with self.config_file() as config_file:
            reader = game.config.reader(config_file)
            for id, path in reader:
                try:
                    with archive.open_library(path) as ar:
                        self.add_gamesystem(ar)
                # bleh
                except (
                OSError, InvalidArchiveError, ExistingLibraryError) as e:
                    log.warning("game system `%s' (at `%s') is invalid: %s", id,
                                path, e)

        return game_systems, last_seen_at

    def save_config(self):
        with self.config_file('w') as config_file:
            writer = game.config.writer(config_file)
            for system in self.systems:
                path = self._last_path[system.id]
                writer.write_system(system, path)


class AppController:
    def __init__(self, qapp, delphi):
        """

        :param qapp: A ``QApplication`` instance (avoids global var shenanigans)
        :param delphi:
        """

        self.qapp = qapp
        self.delphi = delphi
        self.new_campaign_dialog = None
        self.campaign_controller = None
        self.games = GameSystemManager()
        self.games.load_config()

    def show_new_campaign(self):
        dlg = self.new_campaign_dialog = NewCampaignDialog(self.games.systems,
                                                           {})
        dlg.accepted.connect(self.on_new_campaign)
        dlg.newGameSystemRequested.triggered.connect(self.on_add_gamesystem)
        dlg.show()
        dlg.raise_()

    def on_add_gamesystem(self):
        path = get_open_filename(self.new_campaign_dialog,
                                 "Import game archive", filter_=filters.library)
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
        options = self.new_campaign_dialog.options
        # TODO
        game_system = None

        campaign = Campaign(game_system)
        self.on_campaign_loaded(campaign)

    def load_campaign(self, path):
        try:
            campaign = load_campaign(path)
            self.on_campaign_loaded(campaign)
            core.config.appconfig().last_campaign_path = path
        except (OSError, InvalidArchiveError) as e:
            log.error("Cannot load campaign: %s", e)
            display_error(None, "The campaign could not be loaded.")
            # This is hacky, but if the last campaign gave us troubles, then
            # don't constantly annoy the user with a broken campaign on startup.
            if core.config.appconfig().last_campaign_path == path:
                core.config.appconfig().last_campaign_path = ""
            # Kind of annoying, but what else can we do...
            self.show_new_campaign()

    def on_campaign_loaded(self, campaign):
        controller = CampaignController(campaign, self.delphi)
        window = controller.spawn_view()
        window.show()
        window.raise_()
        window.quit.triggered.connect(self.qapp.quit)

    def shutdown(self):
        try:
            self.games.save_config()
        except OSError as e:
            log.error("failed to save gamesystem config: %s", e)
