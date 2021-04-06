
import settings
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage, QPalette, QBrush
from ui import ui_dialog_addons
import odoo_starter
import svg_icon
import sys
import time

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QMainWindow
import logging

logger = logging.getLogger(__name__)
_translate = QtCore.QCoreApplication.translate
LAST_VERSION = 14


# class StartOdooThread(QThread):
#
#     done = pyqtSignal(int, name='done')
#     stdout_signal = pyqtSignal(str, name='stdout')
#
#     def __init__(self, parent=None, version=14, enterprise_path=""):
#         super().__init__(parent)
#         self.version = version
#         self.enterprise_path = enterprise_path
#
#     def run(self):
#         try:
#             starter = odoo_starter.OdooStarter(self.version, self.enterprise_path, self.stdout_signal)
#             starter.init('PyCharm')
#         except Exception as e:
#             logger.error(e)
#             raise e
#         self.done.emit(1)
#         self.quit()


class DialogAddons(QtWidgets.QDialog):

    def __init__(self):
        super().__init__()
        self.ui = ui_dialog_addons.Ui_DialogAddons()
        self.ui.setupUi(self)
        self.setupUi()

    def setupUi(self):

        self.init_combo_version()
        self.ui.push_button_search.setIcon(svg_icon.get_svg_icon("/ui/img/search.svg"))

    def retranslateUi(self, dialog):
        super(DialogAddons, self).retranslateUi(dialog)

    def init_combo_version(self):
        for i in range(8, LAST_VERSION+1):
            self.ui.combo_version.addItem('%s' % i, i)
        self.ui.combo_version.setCurrentText('%s' % LAST_VERSION)



