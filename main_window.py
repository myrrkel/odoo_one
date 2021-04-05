
import settings
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage, QPalette, QBrush
from ui import ui_main_window, wait_overlay_widget
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


class StartOdooThread(QThread):

    done = pyqtSignal(int, name='done')
    stdout_signal = pyqtSignal(str, name='stdout')

    def __init__(self, parent=None, version=14, enterprise_path=""):
        super().__init__(parent)
        self.version = version
        self.enterprise_path = enterprise_path

    def run(self):
        try:
            starter = odoo_starter.OdooStarter(self.version, self.enterprise_path, self.stdout_signal)
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
        self.main_window = main_window
        self.init_combo_version()
        self.wait_overlay = wait_overlay_widget.WaitOverlay(main_window, opacity=50, circle_size=15, nb_dots=9, dot_size=8, color=QtGui.QColor(98, 74, 91))
        self.wait_overlay.hide()


        self.text_log = QtWidgets.QTextEdit(self.verticalWidget)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(98, 73, 91))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(98, 73, 91))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(178, 146, 169))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        self.text_log.setPalette(palette)
        self.text_log.setObjectName("text_log")
        self.horizontal_layout_log.addWidget(self.text_log)
        self.text_log.hide()


        self.checkbox_enterprise.stateChanged.connect(self.onchange_checkbox_enterprise)
        self.checkbox_enterprise.setChecked(bool(settings.get_setting('USE_ENTERPRISE')))
        self.onchange_checkbox_enterprise()

        self.line_edit_enterprise_path.setText(settings.get_setting('ENTERPRISE_PATH'))

        self.push_button_start.setIcon(svg_icon.get_svg_icon("/ui/img/play.svg"))

        self.push_logs.clicked.connect(self.show_logs)

    def retranslateUi(self, main_window):
        super(Ui_MainWindow, self).retranslateUi(main_window)

    def init_combo_version(self):
        for i in range(8, LAST_VERSION+1):
            self.combo_version.addItem('%s' % i, i)
        self.combo_version.setCurrentText('%s' % LAST_VERSION)

    def onchange_checkbox_enterprise(self):
        if self.checkbox_enterprise.isChecked():
            self.line_edit_enterprise_path.show()
        else:
            self.line_edit_enterprise_path.hide()

    def show_logs(self):
        self.text_log.show()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.starter_thread = StartOdooThread()


    def setupUi(self):
        self.ui.setupUi(self)

        self.ui.push_button_start.clicked.connect(self.start_odoo)

    def starter_thread_done(self):
        self.ui.wait_overlay.hide()

    def start_odoo(self):
        self.ui.wait_overlay.show_overlay()
        version = int(self.ui.combo_version.currentText())
        enterprise_path = ""
        if self.ui.checkbox_enterprise.isChecked() and self.ui.line_edit_enterprise_path.text():
            enterprise_path = self.ui.line_edit_enterprise_path.text()
        self.starter_thread = StartOdooThread(self.ui.wait_overlay, version,  enterprise_path)

        self.starter_thread.start()
        self.starter_thread.done.connect(self.starter_thread_done)
        settings.save_setting('USE_ENTERPRISE', self.ui.checkbox_enterprise.isChecked())
        settings.save_setting('ENTERPRISE_PATH', self.ui.line_edit_enterprise_path.text())

    def resizeEvent(self, event):

        self.ui.wait_overlay.resize(event.size())
        event.accept()
