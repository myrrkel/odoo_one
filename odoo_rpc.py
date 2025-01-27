# Copyright (C) 2024 - Michel Perrocheau (https://github.com/myrrkel).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/algpl.html).
import json
import random
import urllib.request
import time


def json_rpc(url, method, params):
    data = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": random.randint(0, 1000000000),
    }
    req = urllib.request.Request(url=url, data=json.dumps(data).encode(), headers={
        "Content-Type": "application/json",
    })
    reply = json.loads(urllib.request.urlopen(req).read().decode('UTF-8'))
    if reply.get("error"):
        raise Exception(reply["error"])
    return reply["result"]


class OdooRpc:

    def __init__(self, host, port, db, user, password, version):

        self.version = version
        self.host = host
        self.port = port
        self.db = db
        self.user = user
        self.password = password
        self.uid = False
        self.url = "http://%s:%s/jsonrpc" % (self.host, self.port)
        self.addon_list = []

        self.wait_for_odoo()

    def login(self):
        self.uid = self.call(self.url, "common", "login", self.db, self.user, self.password)

    def call(self, url, service, method, *args):
        return json_rpc(url, "call", {"service": service, "method": method, "args": args})

    def call_no_arg(self, url, service, method, *args):
        return json_rpc(url, "call", {"service": service, "method": method})

    def call_odoo(self, model, function, args=None):
        if args is None:
            return self.call(self.url, "object", "execute", self.db, self.uid, self.password, model, function)
        return self.call(self.url, "object", "execute", self.db, self.uid, self.password, model, function, *args)

    def read(self, model, rec_id):
        return self.call_odoo(model, 'read', [rec_id])

    def create_user(self, user_name, password):
        self.call_odoo('res.users', 'create', {'name': user_name, 'login': user_name, 'password': password})

    def update_addons_list(self):
        if int(self.version) >= 13:
            self.call_odoo('ir.module.module', 'update_list')
        else:
            self.call_odoo('ir.module.module', 'update_list', [])

        addons_states = self.call_odoo('ir.module.module', 'search_read', [[('name', '!=', False)], ['name', 'state'], 0, 0, "name"])
        self.addon_list = {addon['name']: {'state': addon['state'], 'id': addon['id']} for addon in addons_states}

    def install_addon(self, addon_name):
        if addon_name:
            addon = self.addon_list[addon_name]
            if addon.get('state', False) == 'installed':
                return
            self.call_odoo('ir.module.module', 'button_immediate_install', [addon.get('id')])

    def upgrade_addon(self, addon_name):
        if addon_name:
            addon = self.addon_list[addon_name]
            self.call_odoo('ir.module.module', 'button_immediate_upgrade', [addon.get('id')])

    def wait_for_odoo(self):
        error = ''
        start_time = time.time()
        while (time.time() - start_time) < 60:
            try:
                self.login()
                error = ''
                break
            except Exception as e:
                error = e
                time.sleep(1)

        if error:
            raise error
