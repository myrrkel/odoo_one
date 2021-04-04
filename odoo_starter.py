import subprocess
import os
import docker
import docker_tools as dt
import odoo_conf as oconf
import odoo_rpc
import odoorpc
from github_modules import GithubModules


class OdooStarter(object):
    def __init__(self, version=14, enterprise_path=""):
        self.version = version
        self.enterprise_path = enterprise_path
        self.local_user = os.environ.get("USER")
        self.odoo_version = '%s.0' % version
        # self.enterprise_path = '../enterprise'
        self.odoo_db = "odoo_%s" % version
        if self.enterprise_path:
            self.odoo_db += '_ee'
        self.docker_manager = dt.DockerManager(version, self.odoo_db)


    def start_sudo(self):
        print('Docker need sudo to be installed.')





    def open_odoo_firefox(self, url):
        process = subprocess.call(['firefox',  url],
                                  stdout=subprocess.PIPE, universal_newlines=True)


    def init(self, name, pull=False):

        if not dt.docker_exists():
            if self.local_user != 'root':
                self.start_sudo()
                return False
            dt.install_docker()
            dt.add_users_in_docker_group()

        if not dt.compose_exists():
            dt.install_compose()

        if pull:
            self.docker_manager.pull_images()

        gh_modules = GithubModules()
        gh_modules.load(self.odoo_version)
        if self.enterprise_path:
            gh_modules.git_checkout_enterprise(self.odoo_version, self.enterprise_path)

        addons_path_list = []
        # addons_path_list = gh_modules.addons_path_list
        # addons_path_list.append('extra_addons')
        dt.stop_compose()
        oconf.create_odoo_conf_file(self.version, addons_path_list, enterprise=self.enterprise_path is not False)
        self.docker_manager.stop_odoo_containers()
        dt.create_compose_file(addons_path_list, version=self.version, cmd_params='-d %s' % self.odoo_db, enterprise_path=self.enterprise_path)

        dt.start_compose()
        if not self.docker_manager.odoo_database_exists():
            if int(self.version) <= 8:
                self.docker_manager.create_empty_database()
            dt.create_compose_file(addons_path_list, version=self.version, cmd_params='-d %s -i base' % self.odoo_db,
                                   enterprise_path=self.enterprise_path)
            dt.start_compose()


        ip = self.docker_manager.get_odoo_ip()
        url = "%s:%s/web?db=%s" % (ip, 8069, self.odoo_db)


        orpc = odoo_rpc.OdooRpc(ip, "8069", "odoo_%s" % self.version, "admin", "admin", self.version)
        admin = orpc.read('res.users', 1)
        orpc.update_addons_list()
        self.open_odoo_firefox(url)



if __name__ == '__main__':
    starter = OdooStarter(14, '../enterprise')
    starter.init('PyCharm')
    # init('PyCharm')
