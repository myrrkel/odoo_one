# Copyright (C) 2024 - Michel Perrocheau (https://github.com/myrrkel).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/algpl.html).
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
import colorsys

def version_palette():
    n = 11
    hsv_tuples = [(x * 1.0 / n, 0.6, 0.6) for x in range(n)]
    return list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))

VERSION_PALETTE = version_palette()



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
        stylesheet = '''VersionLabel{border:1px solid rgba(83, 63, 79, 255); border-radius: 8px; background-color: %s;}''' % style_color
        self.setStyleSheet(stylesheet)


class VersionsWidget(QWidget):

    version_palette = []

    def __init__(self, parent=None, versions=None):
        self.versions = versions or []
        QWidget.__init__(self, parent)
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setContentsMargins(2, 0, 0, 0)
        self.grid_layout.setSpacing(2)

        row = 0
        column = 0
        max_columns = 6

        for version in self.versions:
            version_int = int(version.replace('.0', ''))
            version_widget = VersionLabel(str(version_int))
            color = self.get_version_color(version_int)
            version_widget.set_background_color(color)
            self.grid_layout.addWidget(version_widget, row, column)

            column += 1
            if column >= max_columns:
                row += 1
                column = 0

        self.grid_layout.setColumnStretch(max_columns, 1)

        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(100)
        size_policy.setVerticalStretch(0)
        self.setSizePolicy(size_policy)

    def get_version_color(self, version):
        return VERSION_PALETTE[version - 8]


if __name__ == "__main__":

    class MainWindow(QMainWindow):

        def __init__(self, parent=None):
            QMainWindow.__init__(self, parent)

            widget = QWidget(self)
            self.editor = QTextEdit()
            self.editor.setPlainText("This is a test! " * 100)
            layout = QGridLayout(widget)
            layout.addWidget(self.editor)
            button = VersionsWidget(versions=['8.0', '9.0', '10.0', '11.0', '12.0', '13.0', '14.0', '15.0', '16.0', '17.0', '18.0', '19.0', '20.0', '21.0', '22.0', '23.0',  '24.0', '25.0'])
            layout.addWidget(button)

            self.setCentralWidget(widget)


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
