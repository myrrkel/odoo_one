import subprocess
import os
import docker
import docker_tools as dt
import odoo_conf as oconf
import odoo_rpc
import odoorpc


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
    odoo_version = '14.0'

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
            client.images.pull('odoo:%s' % odoo_version)
    except Exception as e:
        print(e)
        pass

    git_addons_repositories = ['https://github.com/myrrkel/odoo_book_publisher_addons.git',
                               'https://github.com/myrrkel/odoo_addons_community.git']
    addon_dirs = []
    for repo in git_addons_repositories:
        addon_dir = repo.split('/')[-1].split('.')[0]
        addon_dirs.append(addon_dir)
        if os.path.isdir(addon_dir):
            process = subprocess.run(['git', 'pull', '--rebase'], cwd='./'+addon_dir,
                             stdout=subprocess.PIPE, universal_newlines=True)
        else:
            process = subprocess.run(['git', 'clone', repo],
                             stdout=subprocess.PIPE, universal_newlines=True)


    oconf.create_odoo_conf_file(addon_dirs)

    dt.create_compose_file(addon_dirs)
    dt.start_compose()
    ip = get_odoo_ip(client)
    url = "%s:%s" % (ip, "8069")

    orpc = odoo_rpc.OdooRpc(ip, "8069", "odoo", "admin", "admin")

    open_odoo_firefox(url)



if __name__ == '__main__':
    init('PyCharm')
