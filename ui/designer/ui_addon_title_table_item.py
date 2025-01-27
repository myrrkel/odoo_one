# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'addon_title_table_item.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QWidget


class Ui_AddonTitle(QWidget):

    def __init__(self, addon=None):
        self.addon = addon
        self.display_name = addon.display_name.strip() if addon else ''
        self.name = addon.name.strip() if addon else ''
        QWidget.__init__(self)

        self.setObjectName("AddonTitle")
        self.resize(126, 29)
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_addon_display_name = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.label_addon_display_name.setFont(font)
        self.label_addon_display_name.setObjectName("label_addon_display_name")
        self.label_addon_display_name.setText(self.display_name)
        self.verticalLayout.addWidget(self.label_addon_display_name)
        self.label_addon_name = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_addon_name.setFont(font)
        self.label_addon_name.setText(self.name)
        self.label_addon_name.setObjectName("label_addon_name")
        self.verticalLayout.addWidget(self.label_addon_name)

        QtCore.QMetaObject.connectSlotsByName(self)

