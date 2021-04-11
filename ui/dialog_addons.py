from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSizePolicy
from ui.designer import ui_addon_title_table_item, ui_dialog_addons
import svg_icon
import addons_lib

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
        self.addons = []
        self.categories = []
        self.users = []
        self.current_version_addons = []
        self.ui = ui_dialog_addons.Ui_DialogAddons()
        self.ui.setupUi(self)
        self.setupUi()

    def show(self):
        if not self.addons:
            lib_addons = addons_lib.AddonsLib()
            self.addons = lib_addons.addons
            self.categories = lib_addons.categories
            self.users = lib_addons.users
            self.show_addons_count()
            self.current_version_changed()
            self.init_combo_categories()
            self.init_combo_users()
        super(DialogAddons, self).show()

    def setupUi(self):
        self.ui.push_button_search.setIcon(svg_icon.get_svg_icon("/ui/img/search.svg"))
        self.ui.push_button_search.setText('')
        self.ui.push_button_search.setMaximumWidth(self.ui.push_button_search.height())
        self.setWindowFlags(Qt.Window)
        self.ui.push_button_search.clicked.connect(self.search)
        self.ui.combo_addons_version.currentIndexChanged.connect(self.current_version_changed)
        self.ui.combo_user.currentIndexChanged.connect(self.search)
        self.ui.combo_category.currentIndexChanged.connect(self.search)
        self.ui.line_edit_search.editingFinished.connect(self.search)

        self.init_combo_addons_version()

    def retranslateUi(self, dialog):
        super(DialogAddons, self).retranslateUi(dialog)

    def init_combo_categories(self):
        for category in self.categories:
            self.ui.combo_category.addItem(category, category)

    def init_combo_users(self):
        for user in self.users:
            self.ui.combo_user.addItem(user, user)

    def init_combo_addons_version(self):
        self.ui.combo_addons_version.addItem('All', 'all')
        for i in range(8, LAST_VERSION+1):
            self.ui.combo_addons_version.addItem('%s' % i, i)

        self.ui.combo_addons_version.setCurrentText('%s' % LAST_VERSION)

    def show_addons_count(self):
        self.ui.label_addons_count.setText('%s community addons' % len(self.addons))

    def show_results_count(self, results_count):
        self.ui.label_result_count.setText('%s results' % results_count)

    def search(self):
        self.show_addons(self.ui.line_edit_search.text())

    def current_version_changed(self):
        self.compute_current_version_addons(self.ui.combo_addons_version.currentData())
        self.search()

    def compute_current_version_addons(self, version_filter='all'):
        if version_filter == 'all':
            self.current_version_addons = self.addons
        else:
            version = '%s.0' % version_filter
            self.current_version_addons = [a for a in self.addons if version in a.versions]

    def show_addons(self, search_string=''):
        self.ui.table_addons.hide()

        addons = self.current_version_addons
        if search_string:
            words = search_string.lower().split(' ')
            addons = [a for a in addons if a.search_words(words)]

        category = self.ui.combo_category.currentData()
        if category:
            addons = [a for a in addons if category in a.categories]

        user = self.ui.combo_user.currentData()
        if user:
            addons = [a for a in addons if user == a.user]

        self.show_results_count(len(addons))
        self.ui.table_addons.setRowCount(0)

        for i, addon in enumerate(addons):
            self.ui.table_addons.insertRow(i)
            self.ui.table_addons.setRowHeight(i, 30)
            self.ui.table_addons.setColumnWidth(0, 300)
            self.ui.table_addons.setColumnWidth(1, 400)

            header = self.ui.table_addons.horizontalHeader()
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
            header.setSectionResizeMode(2, QtWidgets.QHeaderView.Fixed)
            header.setSectionResizeMode(3, QtWidgets.QHeaderView.Fixed)

            title_addon_widget = QtWidgets.QWidget()
            ui_title_addon_widget = ui_addon_title_table_item.Ui_AddonTitle()
            ui_title_addon_widget.setupUi(title_addon_widget)
            ui_title_addon_widget.label_addon_display_name.setText(addon.display_name)
            ui_title_addon_widget.label_addon_name.setText(addon.name)
            self.ui.table_addons.setCellWidget(i, 0, title_addon_widget)

            summary_widget = QtWidgets.QLabel()
            summary_widget.setText(addon.summary)
            size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            size_policy.setHorizontalStretch(100)
            size_policy.setVerticalStretch(100)
            summary_widget.setSizePolicy(size_policy)
            summary_widget.setTextFormat(Qt.RichText)
            summary_widget.setScaledContents(True)
            summary_widget.setWordWrap(True)
            self.ui.table_addons.setCellWidget(i, 1, summary_widget)

        self.ui.table_addons.show()
