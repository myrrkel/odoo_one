# Copyright (C) 2024 - Michel Perrocheau (https://github.com/myrrkel).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/algpl.html).
from github_modules import *
from operator import itemgetter, attrgetter


class Addon:
    categories = set()
    installed = False
    to_install = False
    to_remove = False

    def __init__(self, addon_dict=None):

        self.author = addon_dict['author']
        self.category = addon_dict['category']
        self.display_name = addon_dict['display_name']
        self.name = addon_dict['name']
        self.repository = addon_dict['repository']
        self.summary = addon_dict['summary']
        self.user = addon_dict['user']
        self.versions = addon_dict['versions']

        self.keywords = set(self.display_name.lower().split(' '))
        self.keywords.update(set(self.name.lower().split('_')))
        self.keywords.update(set(self.summary.lower().split(' ')))
        self.compute_categories()

    def compute_categories(self):
        categories = self.category.lower().replace('\\', '/').replace(',', '/').replace(' and ', '/').replace('&', '/').split('/')
        self.categories = set([c.strip().title() for c in categories])

    def search_words(self, words):
        if set(words).issubset(self.keywords):
            return True
        for word in words:
            if not [k for k in self.keywords if word in k]:
                return False
        return True

    def get_github_url(self, version=False):
        if not version:
            version = self.versions[0]
        url = "https://github.com/%s/%s/tree/%s/%s"
        return url % (self.user, self.repository, version, self.name)


class AddonsLib:
    installed_addons = []
    addons = []
    categories = []
    users = []

    def __init__(self, odoo_version='all'):
        self.version = odoo_version
        self.addons = sorted([Addon(m) for m in load_github_modules(odoo_version)], key=attrgetter('display_name'))
        self.compute_categories_users()

    def compute_categories_users(self):
        categories = set()
        users = set()
        for addon in self.addons:
            categories = categories.union(addon.categories)
            users.add(addon.user)

        categories.add('')
        users.add('')
        self.categories = sorted(list(categories))
        self.users = sorted(list(users))



