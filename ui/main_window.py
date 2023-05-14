
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


class StartOdooThread(QThread):

    done = pyqtSignal(int, name='done')
    function_name = 'start_odoo'
    github_access_token = ''
    open_in_browser = False

    def __init__(self, parent=None, function_name=None):
        super().__init__(parent)
        self.parent = parent
        if function_name:
            self.function_name = function_name

    def run(self):
        try:
            if self.function_name == 'start_odoo':
                self.parent.odoo.init(open_in_browser=self.open_in_browser)
            if self.function_name == 'update_addons_list':
                try:
                    self.parent.log_thread.mute_odoo = True
                    self.parent.odoo.update_addons_list(self.github_access_token)
                    self.parent.log_thread.mute_odoo = False
                except Exception as err:
                    self.parent.stdout_signal.emit(str(err))
        except Exception as e:
            logger.error(e)
            raise e
        self.done.emit(1)
        self.quit()


class LogThread(QThread):
    mute_odoo = False
    last_line = ''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        time.sleep(1)
        while True:
            if self.mute_odoo or not hasattr(self.parent, 'odoo'):
                time.sleep(1)
                continue

            if self.parent.odoo and self.parent.odoo.docker_manager.current_process:
                stdout = self.parent.odoo.docker_manager.current_process.stdout
                if stdout:
                    self.parent.stdout_signal.emit(stdout)
            if self.parent.odoo and self.parent.odoo.docker_manager:
                try:
                    logs = self.parent.odoo.get_logs()
                    if logs:
                        last_line = logs.splitlines()[-1]
                        if last_line != self.last_line:
                            self.last_line = last_line
                            self.parent.stdout_signal.emit(logs)
                except Exception as err:
                    logger.error(err)
                    pass
            time.sleep(1)


class Ui_MainWindow(ui_main_window.Ui_MainWindow):

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.odoo = main_window.odoo
        self.widget_dialog_addons = dialog_addons.DialogAddons(main_window)

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
        self.action_database_manager = QtWidgets.QAction(_translate('MainWindow', 'Database Manager'))
        self.tool_menu.addAction(self.action_database_manager)
        self.action_config_database = QtWidgets.QAction(_translate('MainWindow', 'Database configuration'))
        self.tool_menu.addAction(self.action_config_database)
        self.action_update_addons_list = QtWidgets.QAction(_translate('MainWindow', 'Update addons list from Github'))
        self.tool_menu.addAction(self.action_update_addons_list)
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
        for i in range(8, self.odoo.get_last_version()+1):
            self.combo_version.addItem('%s' % i, i)
        self.combo_version.setCurrentText(str(self.odoo.get_last_version()))

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
        self.odoo = odoo_manager.OdooManager(False, '', self.stdout_signal, self)
        self.ui = Ui_MainWindow(self)
        self.starter_thread = StartOdooThread(self)
        self.log_thread = LogThread(self)
        self.log_thread.start()

        self.stdout_signal.connect(self.print_log)

    def setupUi(self):
        self.ui.setupUi(self)
        self.ui.push_button_start.clicked.connect(self.start_and_open_odoo)
        self.ui.push_logs.clicked.connect(self.copy_logs)
        self.ui.action_update_addons_list.triggered.connect(self.update_addons_list)
        self.ui.action_database_manager.triggered.connect(self.database_manager)

    def starter_thread_done(self):
        self.ui.wait_overlay.hide()

    def copy_logs(self):
        cb = QtWidgets.QApplication.clipboard()
        cb.setText(self.ui.text_log.toPlainText())

    def update_addons_list(self):
        self.set_odoo_manager()
        github_access_token = settings.get_setting('github_access_token')
        if not github_access_token:
            dialog = QtWidgets.QInputDialog()
            label = '<html style="font-size:12pt;">GitHub Access Token: %s</html>' % ("&nbsp;" * 30)
            github_access_token, ok = dialog.getText(self, "GitHub", label, QtWidgets.QLineEdit.Normal, '')
            if ok and github_access_token:
                settings.save_setting('github_access_token', github_access_token)

        if github_access_token:
            self.update_addons_list_thread = StartOdooThread(self, function_name='update_addons_list')
            self.update_addons_list_thread.github_access_token = github_access_token
            self.update_addons_list_thread.start()

    def database_manager(self):
        try:
            self.odoo.set_version(self.ui.combo_version.currentData())
            if not self.odoo.check_running_version():
                self.start_odoo(open_in_browser=False)
            try:
                self.odoo.wait_odoo()
            except:
                wait_overlay_widget
                self.odoo.wait_odoo()
            self.odoo.open_odoo_firefox('%s/%s' % (self.odoo.odoo_base_url(), 'database/manager'))
        except Exception as err:
            pass
            return True

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

    def set_odoo_manager(self):
        version = int(self.ui.combo_version.currentText())
        enterprise_path = ""
        if self.ui.checkbox_enterprise.isChecked() and self.ui.line_edit_enterprise_path.text():
            enterprise_path = self.ui.line_edit_enterprise_path.text()

        self.odoo = odoo_manager.OdooManager(version, enterprise_path, self.stdout_signal, self)

    def start_and_open_odoo(self):
        self.start_odoo(open_in_browser=True)

    def start_odoo(self, open_in_browser=True):
        self.log_thread.quit()
        self.ui.wait_overlay.show_overlay()
        self.set_odoo_manager()
        self.starter_thread = StartOdooThread(self)
        self.starter_thread.open_in_browser = open_in_browser
        self.starter_thread.start()
        self.starter_thread.done.connect(self.starter_thread_done)
        settings.save_setting('USE_ENTERPRISE', self.ui.checkbox_enterprise.isChecked())
        settings.save_setting('ENTERPRISE_PATH', self.ui.line_edit_enterprise_path.text())
        self.log_thread = LogThread(self)
        self.log_thread.start()

    def closeEvent(self, event):
        self.log_thread.terminate()
        self.starter_thread.terminate()
        event.accept()
