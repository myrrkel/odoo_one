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
    gh_modules.load(VERSION)

    addon_dirs = []
    oconf.create_odoo_conf_file(addon_dirs)

    dt.create_compose_file(addon_dirs, version=ODOO_VERSION, cmd_params='')

    dt.start_compose()
    if not odoo_database_exists(client):
        dt.create_compose_file(addon_dirs, version=ODOO_VERSION, cmd_params='-d %s -i base' % ODOO_DB)
        dt.start_compose()


    ip = get_odoo_ip(client)
    url = "%s:%s/web?db=%s" % (ip, 8069, ODOO_DB)

    orpc = odoo_rpc.OdooRpc(ip, "8069", "odoo_%s" % VERSION, "admin", "admin")
    admin = orpc.read('res.users', 1)
    open_odoo_firefox(url)



if __name__ == '__main__':
    init('PyCharm')
