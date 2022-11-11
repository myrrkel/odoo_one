
import settings
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from ui.designer import ui_main_window
import odoo_manager
import svg_icon
from ui import dialog_addons, wait_overlay_widget

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QMainWindow
import logging

logger = logging.getLogger(__name__)
_translate = QtCore.QCoreApplication.translate
LAST_VERSION = 16


class StartOdooThread(QThread):

    done = pyqtSignal(int, name='done')

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        try:
            self.parent.log_thread.terminate()
            self.parent.odoo.init()
        except Exception as e:
            logger.error(e)
            raise e
        self.done.emit(1)
        self.quit()


class LogThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        time.sleep(1)
        while True:
            if self.parent.odoo and self.parent.odoo.docker_manager.current_process:
                stdout = self.parent.odoo.docker_manager.current_process.stdout
                if stdout:
                    self.parent.stdout_signal.emit(stdout)
            if self.parent.odoo.docker_manager:
                for container in self.parent.odoo.docker_manager.get_odoo_containers():
                    self.parent.stdout_signal.emit(container.logs().decode())
            time.sleep(1)


class Ui_MainWindow(ui_main_window.Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.widget_dialog_addons = dialog_addons.DialogAddons()

    def setupUi(self, main_window):
        super(Ui_MainWindow, self).setupUi(main_window)
        self.main_window = main_window
        self.init_combo_version()
        self.wait_overlay = wait_overlay_widget.WaitOverlay(main_window, opacity=0, circle_size=15, nb_dots=9,
                                                            dot_size=8, color=QtGui.QColor(198, 174, 191))
        self.wait_overlay.resize(100, 100)
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

        self.checkbox_enterprise.stateChanged.connect(self.onchange_checkbox_enterprise)
        self.checkbox_enterprise.setChecked(bool(settings.get_setting('USE_ENTERPRISE')))
        self.onchange_checkbox_enterprise()

        self.tool_menu = QtWidgets.QMenu(self.main_window)
        self.action_select_database = QtWidgets.QAction(_translate('MainWindow', 'Select database'))
        self.tool_menu.addAction(self.action_select_database)
        self.action_config_database = QtWidgets.QAction(_translate('MainWindow', 'Database configuration'))
        self.tool_menu.addAction(self.action_config_database)
        self.push_tools.setMenu(self.tool_menu)

        self.line_edit_enterprise_path.setText(settings.get_setting('ENTERPRISE_PATH'))

        self.push_button_start.setIcon(svg_icon.get_svg_icon("/ui/img/play.svg"))
        self.push_addons.setIcon(svg_icon.get_svg_icon("/ui/img/store.svg"))
        self.push_update_all.setIcon(svg_icon.get_svg_icon("/ui/img/refresh.svg"))
        self.push_tools.setIcon(svg_icon.get_svg_icon("/ui/img/tools.svg"))
        self.push_logs.setIcon(svg_icon.get_svg_icon("/ui/img/bug.svg"))
        self.push_openugrade.setIcon(svg_icon.get_svg_icon("/ui/img/upgrade.svg"))

        self.push_addons.clicked.connect(self.show_dialog_addons)

    def retranslateUi(self, main_window):
        super(Ui_MainWindow, self).retranslateUi(main_window)

    def init_combo_version(self):
        for i in range(8, LAST_VERSION+1):
            self.combo_version.addItem('%s' % i, i)
        self.combo_version.setCurrentText('%s' % LAST_VERSION)

    def onchange_checkbox_enterprise(self):
        if self.checkbox_enterprise.isChecked():
            self.line_edit_enterprise_path.setDisabled(False)
        else:
            self.line_edit_enterprise_path.setDisabled(True)

    def show_dialog_addons(self):
        self.widget_dialog_addons.show()
        self.widget_dialog_addons.setWindowState(QtCore.Qt.WindowState.WindowActive)


class MainWindow(QMainWindow):
    stdout_signal = pyqtSignal(str, name='stdout')

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.starter_thread = StartOdooThread()
        self.log_thread = LogThread(self)


    def setupUi(self):
        self.ui.setupUi(self)
        self.ui.push_button_start.clicked.connect(self.start_odoo)

    def starter_thread_done(self):
        self.ui.wait_overlay.hide()

    def print_log(self, to_log):
        is_new_log = self.ui.text_log == ''

        sb = self.ui.text_log.verticalScrollBar()
        sb_value = sb.value()
        is_max = sb_value == sb.maximum()
        if not sb.isSliderDown():
            self.ui.text_log.setText(to_log)

        if is_max or is_new_log:
            sb.setValue(sb.maximum())
        else:
            sb.setValue(sb_value)

    def start_odoo(self):
        self.log_thread.quit()
        self.ui.wait_overlay.show_overlay()
        version = int(self.ui.combo_version.currentText())
        enterprise_path = ""
        if self.ui.checkbox_enterprise.isChecked() and self.ui.line_edit_enterprise_path.text():
            enterprise_path = self.ui.line_edit_enterprise_path.text()

        self.odoo = odoo_manager.OdooManager(version, enterprise_path, self.stdout_signal, self)
        self.starter_thread = StartOdooThread(self)
        self.starter_thread.start()
        self.starter_thread.done.connect(self.starter_thread_done)
        self.stdout_signal.connect(self.print_log)
        settings.save_setting('USE_ENTERPRISE', self.ui.checkbox_enterprise.isChecked())
        settings.save_setting('ENTERPRISE_PATH', self.ui.line_edit_enterprise_path.text())

    # def resizeEvent(self, event):
    #
    #     self.ui.wait_overlay.resize(event.size())
    #     event.accept()
