from github_modules import *


class Addon:

    def __init__(self, addon_dict=None):

        self.author = addon_dict['author']
        self.category = addon_dict['category']
        self.display_name = addon_dict['display_name']
        self.name = addon_dict['name']
        self.repository = addon_dict['repository']
        self.summary = addon_dict['summary']
        self.versions = addon_dict['versions']


class AddonsLib:
    installed_addons = []
    addons = []

    def __init__(self, odoo_version='all'):
        self.version = odoo_version
        self.addons = [Addon(m) for m in load_github_modules(odoo_version)]
