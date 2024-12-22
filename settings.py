# Copyright (C) 2024 - Michel Perrocheau (https://github.com/myrrkel).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/algpl.html).
from PyQt5.QtCore import QSettings

settings = QSettings('odoo_one', 'odoo_one')


# if settings.contains('USE_ENTERPRISE'):
#     USE_ENTERPRISE = settings.value('USE_ENTERPRISE', type=bool)
#
# if settings.contains('ENTERPRISE_PATH'):
#     ENTERPRISE_PATH = settings.value('ENTERPRISE_PATH', type=str)


def save_setting(name, value):
    settings.setValue(name, value)


def get_setting(name):
    val = settings.value(name)
    if val == 'true':
        return True
    if val == 'false':
        return False
    return val

