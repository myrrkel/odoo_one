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
    return settings.value(name)

