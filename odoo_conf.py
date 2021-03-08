

def create_odoo_conf_file(path_list = []):
    path_list = ['/opt/'+path for path in path_list]
    addons_path = ','.join(path_list)
    config_file = """[options]
admin_passwd = admin
db_host = db
db_port = 5432
db_user = odoo
db_password = odoo
dbfilter = .*
without_demo = True
addons_path = {path_list}
"""
    config_file  = config_file.format(path_list=addons_path)
    f = open("odoo.conf", "w+")
    f.write(config_file)
    f.close()
