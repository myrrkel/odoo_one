

def create_odoo_conf_file():
    compose = """[options]
admin_passwd = admin
db_host = db
db_port = 5432
db_user = odoo
db_password = odoo
dbfilter = .*
without_demo = True
"""

    f = open("odoo.conf", "w+")
    f.write(compose)
    f.close()
