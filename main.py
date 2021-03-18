import subprocess
import os
import docker
import docker_tools as dt
import odoo_conf as oconf
import odoo_rpc
import odoorpc
from github_modules import GithubModules


local_user = os.environ.get("USER")
ODOO_VERSION = '14.0'
VERSION = ODOO_VERSION.replace('.0', '')
ODOO_DB = "odoo_%s" % VERSION


def start_sudo():
    print('Docker need sudo to be installed.')


def get_odoo_ip(client):
    containers = client.containers.list(filters={'ancestor': 'odoo:%s' % ODOO_VERSION})
    for container in containers:
        ip = container.attrs['NetworkSettings']['Networks']['odoo_one_default']['Gateway']
        return ip


def odoo_database_exists(client):
    containers = client.containers.list(filters={'ancestor': 'postgres:10'})
    for container in containers:
        cmd_res = container.exec_run('psql -U odoo -tAc "SELECT 1 FROM pg_database WHERE datname=\'%s\'" template1' % ODOO_DB)
        return bool(cmd_res.output)


def create_empty_database(client):
    containers = client.containers.list(filters={'ancestor': 'postgres:10'})
    for container in containers:
        cmd_res = container.exec_run('createdb -h 127.0.0.1 -U odoo \'%s\'' % ODOO_DB)
        return bool(cmd_res.output)


def open_odoo_firefox(url):
    process = subprocess.call(['firefox',  url],
                              stdout=subprocess.PIPE, universal_newlines=True)


def init(name, pull=False):

    if not dt.docker_exists():
        if local_user != 'root':
            start_sudo()
            return False
        dt.install_docker()
        dt.add_users_in_docker_group()

    if not dt.compose_exists():
        dt.install_compose()

    client = docker.from_env()
    try:
        if pull:
            client.images.pull('odoo:%s' % ODOO_VERSION)
    except Exception as e:
        print(e)
        pass

    gh_modules = GithubModules()
    gh_modules.load(ODOO_VERSION)

    addons_path_list = gh_modules.addons_path_list
    addons_path_list.append('extra_addons')
    oconf.create_odoo_conf_file(VERSION, addons_path_list)

    dt.create_compose_file(addons_path_list, version=VERSION, cmd_params='-d %s')

    dt.start_compose()
    if not odoo_database_exists(client):
        if int(VERSION) <= 8:
            create_empty_database(client)
        dt.create_compose_file(addons_path_list, version=VERSION, cmd_params='-d %s -i base' %ODOO_DB)
        dt.start_compose()


    ip = get_odoo_ip(client)
    url = "%s:%s/web?db=%s" % (ip, 8069, ODOO_DB)


    orpc = odoo_rpc.OdooRpc(ip, "8069", "odoo_%s" % VERSION, "admin", "admin", VERSION)
    admin = orpc.read('res.users', 1)
    orpc.update_addons_list()
    open_odoo_firefox(url)



if __name__ == '__main__':
    init('PyCharm')
