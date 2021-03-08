import json
import random
import urllib.request


class OdooRpc:

    def __init__(self, host, port, db, user, password):

        self.host = host
        self.port = port
        self.db = db
        self.user = user
        self.password = password

        self.url = "http://%s:%s/jsonrpc" % (self.host, self.port)
        self.uid = self.call(self.url, "common", "login", self.db, self.user, self.password)

    def json_rpc(self, url, method, params):
        data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": random.randint(0, 1000000000),
        }
        req = urllib.request.Request(url=url, data=json.dumps(data).encode(), headers={
            "Content-Type":"application/json",
        })
        reply = json.loads(urllib.request.urlopen(req).read().decode('UTF-8'))
        if reply.get("error"):
            raise Exception(reply["error"])
        return reply["result"]

    def call(self, url, service, method, *args):
        return self.json_rpc(url, "call", {"service": service, "method": method, "args": args})

    def call_odoo(self, model, function, args):
        return self.call(self.url, "object", "execute", self.db, self.uid, self.password, model, function, args)

    def create_user(self, user_name, password):
        self.call_odoo('res.users', 'create', {'name': user_name, 'login': user_name, 'password': password})

