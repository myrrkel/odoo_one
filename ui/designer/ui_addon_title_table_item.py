# Copyright (C) 2024 - Michel Perrocheau (https://github.com/myrrkel).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/algpl.html).
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

