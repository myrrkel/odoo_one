# Copyright (C) 2024 - Michel Perrocheau (https://github.com/myrrkel).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/algpl.html).
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QStyledItemDelegate, QMainWindow, QApplication, QLabel
from PyQt5.QtCore import Qt, QAbstractTableModel, QEvent
from ui.designer import ui_addon_title_table_item, ui_dialog_addons
from ui.versions_widget import VersionsWidget
import svg_icon
import addons_lib
import odoo_manager
import subprocess
import logging
import html

logger = logging.getLogger(__name__)
_translate = QtCore.QCoreApplication.translate

class CustomDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.install_icon = svg_icon.get_svg_icon("/ui/img/install.svg")
        self.remove_icon = svg_icon.get_svg_icon("/ui/img/trash.svg")

    def sizeHint(self, option, index):
        if index.column() == 0:
            addon_title_widget = ui_addon_title_table_item.Ui_AddonTitle(index.data())
            return addon_title_widget.sizeHint()
        elif index.column() == 3:
            versions_widget = VersionsWidget(versions=index.data())
            return versions_widget.sizeHint()

    def paint(self, painter, option, index):
        if index.column() == 0:
            self.paint_addon_title(painter, option, index)
        elif index.column() == 1:
            self.paint_author(painter, option, index)
        elif index.column() == 2:
            self.paint_summary(painter, option, index)
        elif index.column() == 3:
            self.paint_versions(painter, option, index)
        elif index.column() == 4:
            self.paint_actions(painter, option, index)

    def paint_addon_title(self, painter, option, index):
        addon = index.data()
        addon_title_widget = ui_addon_title_table_item.Ui_AddonTitle(addon)
        addon_title_widget.setGeometry(option.rect)
        column_width = option.rect.width()
        addon_title_widget.label_addon_display_name.setMaximumWidth(column_width)
        painter.save()
        painter.translate(option.rect.topLeft())
        addon_title_widget.render(painter)
        painter.restore()

    def paint_author(self, painter, option, index):
        addon = index.data()
        author_widget = QtWidgets.QLabel()
        author_widget.setTextFormat(Qt.PlainText)
        author_widget.setObjectName("AddonAuthor")
        author = 'OCA' if addon.user == 'OCA' else html.escape(addon.author)
        author_widget.setText(author)
        author_widget.setTextFormat(Qt.RichText)
        author_widget.setScaledContents(True)
        author_widget.setWordWrap(True)
        author_widget.setGeometry(option.rect)
        painter.save()
        painter.translate(option.rect.topLeft())
        author_widget.render(painter)
        painter.restore()

    def paint_summary(self, painter, option, index):
        author = index.data()
        summary_widget = QtWidgets.QLabel()
        summary_widget.setTextFormat(Qt.PlainText)
        summary_widget.setObjectName("AddonSummary")
        summary_widget.setText(html.escape(author))
        summary_widget.setTextFormat(Qt.RichText)
        summary_widget.setScaledContents(True)
        summary_widget.setWordWrap(True)
        summary_widget.setGeometry(option.rect)
        painter.save()
        painter.translate(option.rect.topLeft())
        summary_widget.render(painter)
        painter.restore()

    def paint_versions(self, painter, option, index):
        versions = index.data()
        versions_widget = VersionsWidget(versions=versions)
        versions_widget.setGeometry(option.rect)
        painter.save()
        painter.translate(option.rect.topLeft())
        versions_widget.render(painter)
        painter.restore()

    def paint_actions(self, painter, option, index):
        addon = index.data()
        button = QtWidgets.QPushButton('Install')
        button.addon = addon
        if addon.installed or addon.to_install:
            button.setIcon(self.remove_icon)
            button.setText('Remove')
            button.clicked.connect(self.remove_addon)
        else:
            button.setIcon(self.install_icon)
            button.setText('Install')
            button.clicked.connect(self.install_addon)

        button.setGeometry(option.rect)
        painter.save()
        painter.translate(option.rect.topLeft())
        button.render(painter)
        painter.restore()

    def install_addon(self, addon):
        self.parent.gh_modules.add_addon_db_settings(addon.name, addon.user, addon.repository)

    def remove_addon(self, addon):
        self.parent.gh_modules.remove_addon_db_settings(addon.name)

    def editorEvent(self, event, model, option, index):
        if index.column() == 4:
            if event.type() == QEvent.MouseButtonRelease:
                print('Clicked on Item', index.row())
                addon = index.data()
                if addon.installed or addon.to_install:
                    addon.to_remove = True
                    addon.installed = False
                    addon.to_install = False
                    self.remove_addon(addon)
                else:
                    addon.to_remove = False
                    addon.to_install = True
                    self.install_addon(addon)

        if event.type() == QEvent.MouseButtonDblClick:
            print('Double-Clicked on Item', index.row())

        return True


class AddonModel(QAbstractTableModel):
    def __init__(self, addons):
        super().__init__()
        self.addons = addons
        self.column_headers = ["Addon", "Author", "Summary", "Versions", "Actions"]

    def rowCount(self, parent=None):
        return len(self.addons)

    def columnCount(self, parent=None):
        return len(self.column_headers)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.column_headers[section]

    def data(self, index, role=Qt.DisplayRole):
        addon = self.addons[index.row()]
        if role == Qt.DisplayRole:
            if index.column() == 2:
                return addon.summary
            elif index.column() == 3:
                return addon.versions
            else:
                return addon

        elif role == Qt.UserRole:
            return addon
        return addon

class DialogAddons(QtWidgets.QDialog):
    lib_addons = addons_lib.AddonsLib()
    init_combo_addons = False

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.odoo = main_window.odoo if hasattr(main_window, 'odoo') else odoo_manager.OdooManager()
        self.gh_modules = self.odoo.gh_modules
        self.addons = self.lib_addons.addons
        self.categories = []
        self.users = []
        self.installed_modules = []
        self.current_version_addons = []
        self.ui = ui_dialog_addons.Ui_DialogAddons()
        self.ui.setupUi(self)

        self.model = AddonModel(self.addons)
        self.ui.table_addons.setModel(self.model)
        self.ui.table_addons.setItemDelegate(CustomDelegate(self))

        self.ui.table_addons.setColumnWidth(0, 300)
        self.ui.table_addons.setColumnWidth(1, 200)
        self.ui.table_addons.setColumnWidth(2, 400)
        self.ui.table_addons.setColumnWidth(3, 150)
        self.ui.table_addons.setColumnWidth(4, 100)

        self.show_results_count(len(self.addons))
        header = self.ui.table_addons.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.Fixed)

        vertical_header = self.ui.table_addons.verticalHeader()
        vertical_header.setDefaultSectionSize(40)

        self.setupUi()

    def show(self):
        if not self.addons:
            self.addons = self.lib_addons.addons
        self.categories = self.lib_addons.categories
        self.users = self.lib_addons.users
        self.current_version_changed()

        self.show_addons_count()
        self.init_combo_categories()
        self.init_combo_users()
        super(DialogAddons, self).show()

    def setupUi(self):
        self.ui.push_button_search.setIcon(svg_icon.get_svg_icon("/ui/img/search.svg"))
        self.ui.label_icon.setPixmap(svg_icon.get_scaled_svg("/ui/img/store.svg",
                                                             self.ui.label_icon.size(),
                                                             color=svg_icon.purple_dark))
        self.ui.push_button_search.setText('')
        self.ui.push_button_search.setMaximumWidth(self.ui.push_button_search.height())
        self.setWindowFlags(Qt.Window)
        self.init_combo_addons_version()

        self.ui.push_button_search.clicked.connect(self.search)
        self.ui.combo_addons_version.currentIndexChanged.connect(self.current_version_changed)
        self.ui.combo_user.currentIndexChanged.connect(self.search)
        self.ui.combo_category.currentIndexChanged.connect(self.search)
        self.ui.line_edit_search.editingFinished.connect(self.search)
        self.ui.table_addons.doubleClicked.connect(self.open_github_page)


    def retranslateUi(self, dialog):
        super(DialogAddons, self).retranslateUi(dialog)

    def get_current_version(self):
        return self.ui.combo_addons_version.currentData()

    def open_github_page(self, index):
        addon = self.ui.table_addons.model().data(index,Qt.UserRole)
        current_version = self.get_current_version()
        if current_version == 'all':
            version = addon.versions[0]
        else:
            version = odoo_manager.number_to_version(current_version)
        url = addon.get_github_url(version)
        subprocess.call(['firefox', url],
                        stdout=subprocess.PIPE, universal_newlines=True)

    def init_combo_categories(self):
        self.ui.combo_category.blockSignals(True)
        self.ui.combo_category.clear()
        for category in self.categories:
            self.ui.combo_category.addItem(category, category)
        self.ui.combo_category.blockSignals(False)

    def init_combo_users(self):
        self.ui.combo_category.blockSignals(True)
        self.ui.combo_user.clear()
        for user in self.users:
            self.ui.combo_user.addItem(user, user)
        self.ui.combo_category.blockSignals(False)

    def init_combo_addons_version(self):
        self.init_combo_addons = True
        self.ui.combo_addons_version.addItem('All', 'all')
        for i in range(8, self.odoo.get_last_version()+1):
            self.ui.combo_addons_version.addItem('%s' % i, i)

        self.ui.combo_addons_version.setCurrentText('%s' % self.odoo.get_last_version())
        self.init_combo_addons = False

    def show_addons_count(self):
        self.ui.label_addons_count.setText('%s community addons' % len(self.addons))

    def show_results_count(self, results_count):
        self.ui.label_result_count.setText('%s results' % results_count)

    def search(self):
        print("search")
        self.show_addons(self.ui.line_edit_search.text())

    def current_version_changed(self):
        if self.init_combo_addons:
            return
        version = self.get_current_version()
        self.gh_modules.set_version(version)
        if version != 'all':
            self.gh_modules.load(version)
            self.update_installed_addon_list()
        else:
            self.installed_modules = []
        self.compute_current_version_addons(version)
        self.search()

    def update_installed_addon_list(self):
        if self.gh_modules.db_settings:
            modules = self.gh_modules.db_settings['modules']
            self.installed_modules = [m['name'] for m in modules]

    def compute_current_version_addons(self, version_filter='all'):
        if version_filter == 'all':
            self.current_version_addons = self.addons
        else:
            version = '%s.0' % version_filter
            self.current_version_addons = [a for a in self.addons if version in a.versions]

    def show_addons(self, search_string=''):
        self.ui.table_addons.hide()
        self.update_installed_addon_list()
        addons = self.current_version_addons
        if search_string:
            words = search_string.lower().replace('_', ' ').split(' ')
            addons = [a for a in addons if a.search_words(words)]

        category = self.ui.combo_category.currentData()
        if category:
            addons = [a for a in addons if category in a.categories]

        user = self.ui.combo_user.currentData()
        if user:
            addons = [a for a in addons if user == a.user]

        self.show_results_count(len(addons))
        # header = self.ui.table_addons.horizontalHeader()
        # header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        # header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        # header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        # header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        # header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        #
        # vertical_header = self.ui.table_addons.verticalHeader()
        # vertical_header.setDefaultSectionSize(40)

        self.ui.table_addons.setModel(AddonModel(addons))
        self.ui.table_addons.show()

    # def insert_row(self, i, addon):
    #     self.ui.table_addons.insertRow(i)
    #     self.ui.table_addons.setRowHeight(i, 40)
    #     title_addon_widget = QtWidgets.QWidget()
    #     ui_title_addon_widget = ui_addon_title_table_item.Ui_AddonTitle()
    #     ui_title_addon_widget.setupUi(title_addon_widget)
    #     ui_title_addon_widget.label_addon_display_name.setText(addon.display_name)
    #     ui_title_addon_widget.label_addon_name.setText(addon.name)
    #     self.ui.table_addons.setCellWidget(i, 0, title_addon_widget)
    #
    #     summary_widget = QtWidgets.QLabel()
    #     summary_widget.setTextFormat(Qt.PlainText)
    #     summary_widget.setObjectName("AddonSummary")
    #     summary_widget.setText(html.escape(addon.summary))
    #     size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    #     size_policy.setHorizontalStretch(100)
    #     size_policy.setVerticalStretch(100)
    #     summary_widget.setSizePolicy(size_policy)
    #     summary_widget.setTextFormat(Qt.RichText)
    #     summary_widget.setScaledContents(True)
    #     summary_widget.setWordWrap(True)
    #     self.ui.table_addons.setCellWidget(i, 1, summary_widget)
    #
    #     versions = VersionsWidget(versions=addon.versions)
    #     self.ui.table_addons.setCellWidget(i, 2, versions)
    #
    #     if addon.name in self.installed_modules:
    #         install_button = QtWidgets.QPushButton('Remove')
    #         install_button.setIcon(self.trash_icon)
    #         install_button.addon = addon
    #         install_button.clicked.connect(self.remove_addon)
    #         self.ui.table_addons.setCellWidget(i, 3, install_button)
    #     else:
    #         install_button = QtWidgets.QPushButton('Install')
    #         install_button.setIcon(self.install_icon)
    #         install_button.addon = addon
    #         install_button.clicked.connect(self.install_addon)
    #         self.ui.table_addons.setCellWidget(i, 3, install_button)

    # def install_addon(self):
    #     install_button = self.ui.table_addons.focusWidget()
    #     addon = install_button.addon
    #     self.gh_modules.add_addon_db_settings(addon.name, addon.user, addon.repository)
    #     install_button.setText('Remove')
    #     install_button.setIcon(self.trash_icon)
    #     install_button.clicked.connect(self.remove_addon)
    #
    # def remove_addon(self):
    #     install_button = self.ui.table_addons.focusWidget()
    #     addon = install_button.addon
    #     self.gh_modules.remove_addon_db_settings(addon.name)
    #     install_button.setText('Install')
    #     install_button.setIcon(self.install_icon)
    #     install_button.clicked.connect(self.install_addon)


if __name__ == "__main__":
    import sys
    class MainWindow(QMainWindow):

        def __init__(self, parent=None):
            QMainWindow.__init__(self, parent)

            self.odoo = odoo_manager.OdooManager(False, '', None, self)

            widget_dialog_addons = DialogAddons(self.odoo)
            self.setCentralWidget(widget_dialog_addons)


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
