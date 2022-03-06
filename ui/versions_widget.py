#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import colorsys


class VersionLabel(QLabel):
    def __init__(self, *__args):
        QLabel.__init__(self, *__args)
        self.setObjectName("VersionLabel")
        version_size_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        version_size_policy.setHorizontalStretch(0)
        version_size_policy.setVerticalStretch(0)
        self.setSizePolicy(version_size_policy)
        self.setFrameShape(QFrame.Panel)
        self.setLineWidth(1)
        self.setMaximumWidth(24)
        self.setMinimumWidth(24)
        self.setAlignment(Qt.AlignCenter)

    def set_background_color(self, color):
        style_color = 'rgba({r}, {g}, {b}, 255)'.format(r=color[0] * 255, g=color[1] * 255, b=color[2] * 255)
        stylesheet = 'VersionLabel {background-color: %s;}' % style_color
        self.setStyleSheet(stylesheet)


class VersionsWidget(QWidget):

    version_palette = []

    def __init__(self, parent=None, versions=None):
        QWidget.__init__(self, parent)
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setContentsMargins(2, 0, 0, 0)
        self.h_layout.setSpacing(2)

        self.init_version_palette()

        for version in versions:
            version_int = int(version.replace('.0', ''))
            version_widget = VersionLabel(str(version_int))
            color = self.get_version_color(version_int)
            version_widget.set_background_color(color)
            self.h_layout.addWidget(version_widget)

        self.h_layout.addWidget(QWidget())
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(100)
        size_policy.setVerticalStretch(0)
        self.setSizePolicy(size_policy)

    def init_version_palette(self):
        n = 10
        hsv_tuples = [(x * 1.0 / n, 0.6, 0.6) for x in range(n)]
        self.version_palette = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))

    def get_version_color(self, version):
        return self.version_palette[version - 8]


if __name__ == "__main__":

    class MainWindow(QMainWindow):

        def __init__(self, parent=None):
            QMainWindow.__init__(self, parent)

            widget = QWidget(self)
            self.editor = QTextEdit()
            self.editor.setPlainText("This is a test! " * 100)
            layout = QGridLayout(widget)
            layout.addWidget(self.editor)
            button = VersionsWidget(versions=['10', '11', '13'])
            layout.addWidget(button)

            self.setCentralWidget(widget)


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
