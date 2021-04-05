#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from PyQt5 import QtGui, QtSvg
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QFile, QXmlStreamReader, QByteArray, QTextStream
import os

purple = QtGui.QColor(135, 90, 123)  # html : #875A7B
purple_dark = QtGui.QColor(98, 73, 91)  # html : #62495B
dir_path = os.path.dirname(os.path.realpath(__file__))


def get_svg_icon(file_name):
    return QtGui.QIcon(get_colored_svg(file_name))


def get_colored_svg(file_name, color_to_replace='black', color=purple):
    svg = QtGui.QPixmap(dir_path + file_name)
    mask = svg.createMaskFromColor(QtGui.QColor(color_to_replace), Qt.MaskOutColor)
    svg.fill(color)
    svg.setMask(mask)
    return svg


