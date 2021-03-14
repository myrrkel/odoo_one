import json
import random
import urllib.request
import time


class OdooRpc:

    def __init__(self, host, port, db, user, password):

        self.host = host
        self.port = port
        self.db = db
        self.user = user
        self.password = password
        self.uid = False
        self.url = "http://%s:%s/jsonrpc" % (self.host, self.port)

        self.wait_for_odoo()

    def json_rpc(self, url, method, params):
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

    def login(self):
        self.uid = self.call(self.url, "common", "login", self.db, self.user, self.password)

    def call(self, url, service, method, *args):
        return self.json_rpc(url, "call", {"service": service, "method": method, "args": args})

    def call_odoo(self, model, function, args):
        return self.call(self.url, "object", "execute", self.db, self.uid, self.password, model, function, args)

    def read(self, model, rec_id):
        return self.call_odoo(model, 'read', [rec_id])

    def create_user(self, user_name, password):
        self.call_odoo('res.users', 'create', {'name': user_name, 'login': user_name, 'password': password})

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
