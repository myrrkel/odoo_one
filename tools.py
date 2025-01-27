# Copyright (C) 2024 - Michel Perrocheau (https://github.com/myrrkel).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/algpl.html).


def version_to_number(version):
    return str(version).replace('.0', '')


def number_to_version(number_version):
    return '%s.0' % number_version

