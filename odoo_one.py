#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ui import main_window
import logging
import getopt
import sys
from PyQt5 import QtWidgets

root_logger = logging.getLogger()
root_logger.setLevel("INFO")
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root_logger.addHandler(handler)
logger = logging.getLogger(__name__)


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdp:s:", ["help", "debug", "db-path=", "style="])
    except getopt.GetoptError as e:
        logger.error(e)
        print_help()
        sys.exit(2)

    db_path = ''
    style_name = ''
    for opt, arg in opts:
        if opt in ("-d", "--debug"):
            root_logger.setLevel("DEBUG")
            logger.debug("Debug mode ON")
        elif opt in ("-p", "--db-path"):
            db_path = arg
        elif opt in ("-s", "--style"):
            style_name = arg
        elif opt in ("-h", "--help"):
            print_help()
            sys.exit()

    sys.argv = [sys.argv[0]]
    logger.info("Odoo One starting...")
    app = QtWidgets.QApplication(sys.argv)

    app.setApplicationName("Odoo One")

    # logger.info("Loading translations...")
    # tr = translators(app)
    # localeLanguage = QtCore.QLocale.system().name()
    # tr.installTranslators(localeLanguage)

    ui_main = main_window.MainWindow()
    ui_main.setupUi()
    ui_main.show()

    stylesheet = """
    
        MainWindow,DialogAddons {
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0.0944206 rgba(153, 102, 139, 255), stop:0.896996 rgba(83, 63, 79, 255));
        }
        QPushButton,QComboBox {
            background-color: rgba(178, 146, 169, 255);
            color: rgba(135, 90, 123, 255);
            height: 20;
        }

        QHeaderView {
            background-color: rgba(178, 146, 169, 255);
            color: rgba(83, 63, 79, 255);
        }
        
        
        QTableWidget {
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0.0944206 rgba(153, 102, 139, 255), stop:0.896996 rgba(83, 63, 79, 255));
        }
        
        QLabel#label_version {
            color: white;
        }
        
        
        QLineEdit {
            background-color: rgba(178, 146, 169, 255);
            color: rgba(98, 73, 91, 255);
            height: 20;
        }

        
    """
    app.setStyleSheet(stylesheet)

    app.exec()



    sys.exit()


def print_help():
    help_str = '''
    
#########################    
#    Odoo One Help      #
#########################

    Parameters:
        -d, --debug:       Enable debug mode
        -s, --style:       Set Qt Style (Windows, Fusion...)
        -p, --db-path:     Set the database file path (~/.local/share/pyzik/data/pyzik.db)
        -h, --help:        Display help
        
    '''
    logger.info(help_str)


if __name__ == "__main__":
    main()
