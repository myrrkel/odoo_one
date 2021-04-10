# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialog_addons.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_DialogAddons(object):
    def setupUi(self, DialogAddons):
        DialogAddons.setObjectName("DialogAddons")
        DialogAddons.resize(873, 437)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DialogAddons.sizePolicy().hasHeightForWidth())
        DialogAddons.setSizePolicy(sizePolicy)
        self.gridLayout = QtWidgets.QGridLayout(DialogAddons)
        self.gridLayout.setObjectName("gridLayout")
        self.main_widget = QtWidgets.QWidget(DialogAddons)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.main_widget.sizePolicy().hasHeightForWidth())
        self.main_widget.setSizePolicy(sizePolicy)
        self.main_widget.setObjectName("main_widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.main_widget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_version = QtWidgets.QLabel(self.main_widget)
        font = QtGui.QFont()
        font.setFamily("FreeSans")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label_version.setFont(font)
        self.label_version.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_version.setObjectName("label_version")
        self.horizontalLayout.addWidget(self.label_version, 0, QtCore.Qt.AlignRight)
        self.combo_version = QtWidgets.QComboBox(self.main_widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.combo_version.sizePolicy().hasHeightForWidth())
        self.combo_version.setSizePolicy(sizePolicy)
        self.combo_version.setMinimumSize(QtCore.QSize(70, 0))
        self.combo_version.setMaximumSize(QtCore.QSize(70, 16777215))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.combo_version.setFont(font)
        self.combo_version.setObjectName("combo_version")
        self.horizontalLayout.addWidget(self.combo_version)
        self.line_edit_search = QtWidgets.QLineEdit(self.main_widget)
        self.line_edit_search.setMinimumSize(QtCore.QSize(150, 0))
        self.line_edit_search.setMaximumSize(QtCore.QSize(300, 16777215))
        self.line_edit_search.setObjectName("line_edit_search")
        self.horizontalLayout.addWidget(self.line_edit_search)
        self.push_button_search = QtWidgets.QPushButton(self.main_widget)
        self.push_button_search.setAutoDefault(False)
        self.push_button_search.setObjectName("push_button_search")
        self.horizontalLayout.addWidget(self.push_button_search)
        self.widget = QtWidgets.QWidget(self.main_widget)
        self.widget.setObjectName("widget")
        self.horizontalLayout.addWidget(self.widget)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.table_addons = QtWidgets.QTableWidget(self.main_widget)
        self.table_addons.setMinimumSize(QtCore.QSize(800, 0))
        self.table_addons.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table_addons.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table_addons.setCornerButtonEnabled(False)
        self.table_addons.setObjectName("table_addons")
        self.table_addons.setColumnCount(7)
        self.table_addons.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.table_addons.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.table_addons.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.table_addons.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.table_addons.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.table_addons.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.table_addons.setHorizontalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.table_addons.setHorizontalHeaderItem(6, item)
        self.table_addons.horizontalHeader().setVisible(True)
        self.table_addons.horizontalHeader().setHighlightSections(True)
        self.table_addons.verticalHeader().setVisible(False)
        self.verticalLayout.addWidget(self.table_addons)
        self.gridLayout.addWidget(self.main_widget, 0, 0, 1, 1)

        self.retranslateUi(DialogAddons)
        QtCore.QMetaObject.connectSlotsByName(DialogAddons)

    def retranslateUi(self, DialogAddons):
        _translate = QtCore.QCoreApplication.translate
        DialogAddons.setWindowTitle(_translate("DialogAddons", "Odoo One - Community Addons"))
        self.label_version.setText(_translate("DialogAddons", "Version"))
        self.push_button_search.setText(_translate("DialogAddons", "Search"))
        item = self.table_addons.horizontalHeaderItem(0)
        item.setText(_translate("DialogAddons", "Name"))
        item = self.table_addons.horizontalHeaderItem(1)
        item.setText(_translate("DialogAddons", "Summary"))
        item = self.table_addons.horizontalHeaderItem(2)
        item.setText(_translate("DialogAddons", "Provider"))
        item = self.table_addons.horizontalHeaderItem(3)
        item.setText(_translate("DialogAddons", "Repository"))
        item = self.table_addons.horizontalHeaderItem(4)
        item.setText(_translate("DialogAddons", "Versions"))
        item = self.table_addons.horizontalHeaderItem(5)
        item.setText(_translate("DialogAddons", "State"))
        item = self.table_addons.horizontalHeaderItem(6)
        item.setText(_translate("DialogAddons", "Action"))