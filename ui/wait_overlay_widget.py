#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import sys
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class WaitOverlay(QWidget):
    timer = 0

    def __init__(self, parent=None, nb_dots=15, dot_size=10, circle_size=30, color=None, opacity=40, hide_on_click=False):

        QWidget.__init__(self, parent)
        self.counter = 0
        self.parent = parent
        self.nb_dots = nb_dots
        self.dot_size = dot_size
        self.circle_size = circle_size
        self.hide_on_click = hide_on_click

        if color is None:
            self.color = QColor(100, 100, 100)
        else:
            self.color = color

        self.colorLight = self.color.lighter(150)
        self.colorLight.setAlpha(200)

        self.opacity = opacity

        palette = QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)
        self.setPalette(palette)

    def paintEvent(self, event=None):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(event.rect(), QBrush(QColor(255, 255, 255, self.opacity)))
        painter.setPen(QPen(Qt.NoPen))
        margin = 20

        for i in range(self.nb_dots):
            if self.counter % self.nb_dots == i:
                painter.setBrush(QBrush(self.color))
            else:
                painter.setBrush(QBrush(self.colorLight))

            painter.drawEllipse(
                int(self.circle_size + 30 + self.circle_size * math.cos(2 * math.pi * i / self.nb_dots) - self.dot_size/2),
                int(self.circle_size + 23 + self.circle_size * math.sin(2 * math.pi * i / self.nb_dots) - self.dot_size/2),
                self.dot_size, self.dot_size)

        painter.end()

    def showEvent(self, event):
        event.accept()

    def show_overlay(self):
        if self.timer == 0:
            self.timer = self.startTimer(int(1000 / self.nb_dots))

        self.show()

    def timerEvent(self, event):

        self.counter += 1
        self.update()

    def mouseReleaseEvent(self, event):
        if self.hide_on_click:
            self.hide()


if __name__ == "__main__":

    class MainWindow(QMainWindow):

        def __init__(self, parent=None):
            QMainWindow.__init__(self, parent)

            widget = QWidget(self)
            self.editor = QTextEdit()
            self.editor.setPlainText("This is a test! " * 100)
            layout = QGridLayout(widget)
            layout.addWidget(self.editor)
            button = QPushButton("Wait")
            layout.addWidget(button)

            self.setCentralWidget(widget)
            self.overlay = WaitOverlay(self.centralWidget(), hide_on_click=True)
            self.overlay.hide()
            button.clicked.connect(self.overlay.show_overlay)

        def resizeEvent(self, event):
            self.overlay.resize(event.size())
            event.accept()


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
