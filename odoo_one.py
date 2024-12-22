from ui import main_window
import logging
import getopt
import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import QFile

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
        opts, args = getopt.getopt(sys.argv[1:], "hd", ["help", "debug"])
    except getopt.GetoptError as e:
        logger.error(e)
        print_help()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-d", "--debug"):
            root_logger.setLevel("DEBUG")
            logger.debug("Debug mode ON")
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

    stylesheet_file = QFile("ui/stylesheet.qss")
    stylesheet_file.open(QFile.ReadOnly)
    stylesheet = str(stylesheet_file.readAll(), 'utf-8')
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
        -h, --help:        Display help
        
    '''
    logger.info(help_str)


if __name__ == "__main__":
    main()
