import argparse
import logging
import sys
import traceback

from PyQt5.QtWidgets import QApplication

from PyQt5.QtWidgets import QMainWindow

app = None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("module_name")
    args = parser.parse_args(sys.argv[1:])
    logging.basicConfig(level=logging.DEBUG)
    try:
        app_name = "dmclient test harness"
        global app
        app = QApplication(sys.argv)
        app.setApplicationName(app_name)

        main_window = QMainWindow()
        main_window.setWindowTitle(app_name)
        import ui.widgets.icons_rc

        ns = __import__(args.module_name, globals(), locals(), ('guitest_main',))
        guitest_main = ns.guitest_main
        guitest_main(main_window)

        main_window.show()
        app.exec()
    except ImportError as e:
        traceback.print_exc(file=sys.stderr)
        print("failed to load module {}: {}"
              .format(args.module_name, e),
              file=sys.stderr)


if __name__ == '__main__':
    main()
