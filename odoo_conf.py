def create_odoo_conf_file(version, path_list=[], enterprise=False):

    if int(version) >= 11:
        default_path_list = ["/usr/lib/python3/dist-packages/odoo/addons"]
    else:
        default_path_list = ["/usr/lib/python2.7/dist-packages/odoo/addons"]
    if enterprise:
        default_path_list.append('/opt/enterprise')
    path_list = ['/opt/' + path for path in path_list]
    path_list = default_path_list + path_list

    addons_path = ','.join(path_list)
    config_file = """[options]
admin_passwd = admin
db_host = db
db_port = 5432
db_user = odoo
db_password = odoo
dbfilter = .*
without_demo = True
data_dir = /var/lib/odoo
addons_path = {path_list}
"""
    config_file = config_file.format(path_list=addons_path)
    f = open("odoo.conf", "w+")
    f.write(config_file)
    f.close()
