import subprocess
import os
import docker
import docker_tools as dt
import odoo_conf as oconf
import odoo_rpc


local_user = os.environ.get("USER")


def start_sudo():
    print('Docker need sudo to be installed.')


def get_odoo_ip(client):
    containers = client.containers.list(filters={'ancestor': 'odoo:14.0'})
    for container in containers:
        ip = container.attrs['NetworkSettings']['Networks']['odoo_one_default']['Gateway']
        return ip


def open_odoo_firefox(url):
    process = subprocess.call(['firefox', url],
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
            client.images.pull('odoo:14.0')
    except Exception as e:
        print(e)
        pass

    oconf.create_odoo_conf_file()

    dt.create_compose_file()
    dt.start_compose()
    ip = get_odoo_ip(client)
    url = "%s:%s" % (ip, "8069")

    orpc = odoo_rpc.OdooRpc(ip, "8069", "odoo", "admin", "admin")
    #orpc.create_user('Michel', 'admin')

    open_odoo_firefox(url)



if __name__ == '__main__':
    init('PyCharm')
