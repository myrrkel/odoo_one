from github_modules import *


class Addon:

    def __init__(self, addon_dict=None):

        self.author = addon_dict['author']
        self.category = addon_dict['category']
        self.display_name = addon_dict['display_name']
        self.name = addon_dict['name']
        self.repository = addon_dict['repository']
        self.summary = addon_dict['summary']
        self.user = addon_dict['user']
        self.versions = addon_dict['versions']
        self.words_set = set(self.display_name.lower().split(' '))
        self.words_set.update(set(self.name.lower().split('_')))
        self.words_set.update(set(self.summary.lower().split(' ')))

    def search_words(self, words):
        return set(words).issubset(self.words_set)


class AddonsLib:
    installed_addons = []
    addons = []

    def __init__(self, odoo_version='all'):
        self.version = odoo_version
        self.addons = [Addon(m) for m in load_github_modules(odoo_version)]
