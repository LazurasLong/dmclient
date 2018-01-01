#!/usr/bin/env python3.6
# dmclient.py
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

import argparse
import faulthandler
import itertools
import json
import logging
import logging.handlers
import sys
import traceback

from core import attrs
from core.config import *

_app = None
log = None


def excepthook(type_, value, tb):
    # There is much to do in this department.
    # For now, we can just prevent program abort if the PyQt
    # event loop thread tracebacks due to programmer error.
    print("Unhandled exception:", file=sys.stderr, flush=False)
    traceback.print_tb(tb)
    print("{}: {}".format(type_.__name__, value), file=sys.stderr, flush=True)


class LoggerSpec:
    def __init__(self, specstr):
        self.name, level = specstr.split('=')
        try:
            self.level = getattr(logging, level.upper())
        except AttributeError:
            raise argparse.ArgumentError("invalid logger level `%s'".format(level))


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description=APP_DESCRIPTION,
    )
    parser.add_argument("--disable-oracle",
                        action="store_true",
                        help="Disable the multi-process search indexer.")
    parser.add_argument("--logfile",
                        default=os.path.join(APP_PATH, "dmclient.log"),
                        help="Override default log file.",
                        metavar="FILE")
    parser.add_argument("--log",
                        action="append",
                        help="Specify logger level.",
                        metavar="<log>=<level>",
                        dest="loggers",
                        type=LoggerSpec,
                        default=[],
                        nargs='+')
    parser.add_argument("campaign",
                        nargs='?',
                        help="open CAMPAIGN on startup")
    return parser.parse_args(argv)


def init_logging(args):
    handler = logging.handlers.RotatingFileHandler(args.logfile,
                                                   maxBytes=2 * 1024 * 1024,
                                                   backupCount=8,
                                                   encoding='utf-8')
    stderr_handler = logging.StreamHandler(sys.stderr)
    logging.basicConfig(handlers=[handler, stderr_handler],
                        format="%(asctime)s %(levelname)-7s "
                               "%(name)-16s  %(message)s",
                        level=logging.DEBUG if __debug__ else logging.INFO)
    for logger in itertools.chain.from_iterable(args.loggers):
        logging.getLogger(logger.name).setLevel(logger.level)
    global log
    log = logging.getLogger("dmclient")


def init_appdirs():
    for dir_ in [APP_PATH, CONFIG_PATH, TMP_PATH]:
        try:
            os.mkdir(dir_)
        except FileExistsError:
            pass
        except OSError as e:
            raise Exception("Could not create essential foldier %s: %s" % (dir_, e))


def init_config():
    try:
        decoder = json.JSONDecoder()
        with open(os.path.join(CONFIG_PATH, "config.json")) as f:
            parsed_config = decoder.decode(f.read())
        if not isinstance(parsed_config, dict):
            raise ValueError("malformed config file (not a dict?)")
        appconfig().update(parsed_config)
    except (OSError, ValueError) as e:
        log.error("failed to load config file: %s", e)


def save_config(config):
    try:
        encoder = json.JSONEncoder()
        encoded = encoder.encode(attrs(config))
        with open(os.path.join(CONFIG_PATH, "config.json"), 'w') as f:
            print(encoded, file=f)
    except TypeError as e:
        log.fatal("*** config object appears to have been corrupted: %s", e)
    except OSError as e:
        log.error("failed to save config file: %s", e)


def main():
    sys.excepthook = excepthook
    faulthandler.enable()

    delphi, app_controller = None, None

    try:
        args = parse_args(sys.argv[1:])

        init_appdirs()
        init_logging(args)
        log.debug("hello, world")
        init_config()
        config = appconfig()

        log.debug("initialise oracle zygote")
        from oracle import spawn_zygote
        oracle_zygote = spawn_zygote(args)

        log.debug("initialise Qt")
        from PyQt5.QtGui import QIcon
        from PyQt5.QtWidgets import QApplication

        global _app
        _app = QApplication(sys.argv)
        _app.setApplicationName(APP_NAME)
        _app.setApplicationDisplayName(APP_NAME)
        _app.setWindowIcon(QIcon(APP_ICON_PATH))
        _app.setOrganizationDomain(APP_URL)
        _app.setApplicationVersion(APP_VERSION)
        _app.setQuitOnLastWindowClosed(True)

        if __debug__:
            log.debug("initialise hacks")
            from core.hacks import install_hacks
            install_hacks()

        log.debug("initialise UI")
        import ui

        log.debug("initialise controllers")
        from core.app import AppController
        app_controller = AppController(args, _app, oracle_zygote)

        if args.campaign:
            app_controller.load_campaign(args.campaign)
        elif config.open_last_campaign and config.last_campaign_path:
            app_controller.load_campaign(config.last_campaign_path)
        else:
            app_controller.show_new_campaign()

        log.debug("Qt app exec")
        _app.exec()

    except Exception:
        # TODO: "dmclient has encountered.." etc. etc.
        traceback.print_exc(file=sys.stderr)

    finally:
        if app_controller:
            app_controller.shutdown()
        save_config(appconfig())
        if log:  # None if there was a CLI error
            log.debug("goodbye")
            logging.shutdown()


if __name__ == '__main__':
    main()
