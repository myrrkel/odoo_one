from PyQt5 import QtCore, QtGui, QtWidgets
from ui import ui_main_window, wait_overlay_widget
import odoo_starter
import sys
import time

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QMainWindow
import logging

logger = logging.getLogger(__name__)
_translate = QtCore.QCoreApplication.translate
LAST_VERSION = 14


class StartOdooThread(QThread):

    done = pyqtSignal(int, name='done')

    def __init__(self, parent=None, version=14, enterprise_path=""):
        super().__init__(parent)
        self.version = version
        self.enterprise_path = enterprise_path


    def run(self):
        try:
            starter = odoo_starter.OdooStarter(self.version, self.enterprise_path)
            starter.init('PyCharm')
        except Exception as e:
            logger.error(e)
            raise e
        self.done.emit(1)
        self.quit()


class Ui_MainWindow(ui_main_window.Ui_MainWindow):
    def __init__(self):
        super().__init__()

    def setupUi(self, main_window):
        super(Ui_MainWindow, self).setupUi(main_window)
        self.init_combo_version()
        self.wait_overlay = wait_overlay_widget.WaitOverlay(self.centralwidget, background_opacity=200)
        self.wait_overlay.hide()

    def retranslateUi(self, main_window):
        super(Ui_MainWindow, self).retranslateUi(main_window)

    def init_combo_version(self):
        for i in range(8, LAST_VERSION+1):
            self.combo_version.addItem('%s' % i, i)
        self.combo_version.setCurrentText('%s' % LAST_VERSION)




class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.starter_thread = StartOdooThread()


    def setupUi(self):
        self.ui.setupUi(self)
        # self.ui.wait_overlay = wait_overlay_widget.WaitOverlay(self.centralWidget())

        self.ui.push_button_start.clicked.connect(self.start_odoo)

    def starter_thread_done(self):
        self.ui.wait_overlay.hide()

    def start_odoo(self):
        self.ui.wait_overlay.show_overlay()
        # starter = odoo_starter.OdooStarter(,)
        # starter.init('PyCharm')

        self.starter_thread = StartOdooThread(self.ui.wait_overlay, int(self.ui.combo_version.currentText()), '../enterprise')

        self.starter_thread.start()
        self.starter_thread.done.connect(self.starter_thread_done)
        # self.wait_overlay.hide()

    def resizeEvent(self, event):

        self.ui.wait_overlay.resize(event.size())
        event.accept()
