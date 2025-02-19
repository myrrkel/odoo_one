# Copyright (C) 2024 - Michel Perrocheau (https://github.com/myrrkel).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/algpl.html).
import logging
import os
import webbrowser
import install_docker
import docker_manager
import odoo_conf as oconf
import odoo_rpc
from github_modules import GithubModules
from tools import number_to_version

logger = logging.getLogger(__name__)


class OdooManager(object):

    def __init__(self, version=False, enterprise_path="", stdout_signal=None, main_window=None):
        self.version = version or self.get_last_version()
        self.enterprise_path = enterprise_path
        self.local_user = os.environ.get("USER")
        self.odoo_version = '%s.0' % self.version
        self.odoo_db = "odoo_%s" % self.version
        if self.enterprise_path:
            self.odoo_db += '_ee'
        try:
            self.docker_manager = docker_manager.DockerManager(self.version, self.odoo_db, stdout_signal)
        except Exception as err:
            logger.error(err, exc_info=True)
            self.docker_manager = False
        self.stdout_signal = stdout_signal
        self.main_window = main_window
        self.gh_modules = GithubModules(odoo=self)
        self.gh_modules.stdout_signal = stdout_signal
        self.gh_modules.print_stdout = self.print_stdout
        self.gh_modules.load(self.version, clone=True)

    def docker_exists(self):
        return self.docker_manager and self.docker_manager.client and self.docker_manager.docker_exists()

    def _check_docker(func):
        def wrapper(self, *args, **kwargs):
            if not self.docker_exists():
                return
            return func(self, *args, **kwargs)

        return wrapper

    def get_last_version(self):
        return 18

    def get_all_versions(self):
        return ['%0.1f' % v for v in range(8, self.get_last_version() + 1).__reversed__()]

    def set_version(self, version=''):
        self.version = int(version)
        self.odoo_version = number_to_version(self.version)

    def start_sudo(self):
        print('Docker need sudo to be installed.')

    def print_stdout(self, msg):
        if self.stdout_signal:
            self.stdout_signal.emit(msg)
        else:
            print(msg)

    def update_addons_list(self, access_token):
        self.print_stdout('Start addons list update...')
        self.gh_modules.access_token = access_token
        self.gh_modules.init_github()
        self.gh_modules.generate_json_file(self.odoo_version)
        self.gh_modules.generate_all_github_modules_file()
        self.print_stdout('Addons list update done.')

    @_check_docker
    def init(self, pull=False, open_in_browser=False):
        self.print_stdout('Start Odoo...')
        if not self.docker_manager.docker_exists():
            if self.local_user != 'root':
                self.start_sudo()
                return False
            install_docker.install_docker()
            install_docker.add_users_in_docker_group()
        if not self.docker_manager.client:
            return False

        if pull:
            self.docker_manager.pull_images()

        self.gh_modules.load(self.odoo_version)
        if self.enterprise_path:
            self.gh_modules.git_checkout_enterprise(self.odoo_version, self.enterprise_path)

        addons_path_list = self.gh_modules.addons_path_list
        addons_path_list.append('extra_addons')
        self.docker_manager.stop_compose()
        oconf.create_odoo_conf_file(self.version, addons_path_list, enterprise=self.enterprise_path != '',
                                    db_container=self.docker_manager.get_db_container_name())
        self.docker_manager.stop_odoo_containers()
        self.docker_manager.create_docker_file(self.version, self.gh_modules.external_dependencies)
        self.docker_manager.create_compose_file(addons_path_list,
                                                version=self.version,
                                                cmd_params='-d %s' % self.odoo_db,
                                                enterprise_path=self.enterprise_path)

        self.docker_manager.start_compose()

        if not self.docker_manager.odoo_database_exists():
            if int(self.version) <= 8:
                self.docker_manager.create_empty_database()
            self.docker_manager.create_docker_file(self.version, self.gh_modules.external_dependencies)
            self.docker_manager.create_compose_file(addons_path_list,
                                                    version=self.version,
                                                    cmd_params='-d %s -i base' % self.odoo_db,
                                                    enterprise_path=self.enterprise_path)
            self.docker_manager.start_compose()
        try:
            self.wait_odoo()
            if open_in_browser:
                webbrowser.open(self.odoo_start_url(), new=2)
        except Exception as err:
            logger.error(err)
            pass

    @_check_docker
    def odoo_ip(self):
        return self.docker_manager.get_odoo_ip()

    @_check_docker
    def odoo_base_url(self):
        ip = self.odoo_ip()
        if not ip:
            logger.info('Restarting Odoo Server...')
            self.init()
            return self.odoo_base_url()

        return "%s:%s/web" % (ip, docker_manager.DEFAULT_PORT)

    @_check_docker
    def odoo_start_url(self):
        return "%s?db=%s" % (self.odoo_base_url(), self.odoo_db)

    @_check_docker
    def get_odoo_rpc(self):
        return odoo_rpc.OdooRpc(self.odoo_ip(),
                                docker_manager.DEFAULT_PORT,
                                self.odoo_db,
                                "admin",
                                "admin",
                                self.version)

    @_check_docker
    def check_running_version(self):
        return self.docker_manager.get_odoo_running_version() == number_to_version(self.version)

    @_check_docker
    def wait_odoo(self):
        orpc = self.get_odoo_rpc()
        admin = orpc.read('res.users', 1)
        orpc.update_addons_list()
        for addon in self.gh_modules.addons:
            orpc.install_addon(addon)

    @_check_docker
    def get_logs(self):
        try:
            return self.docker_manager.get_odoo_logs()
        except Exception as err:
            pass
            logger.error(err)
            return ''


if __name__ == '__main__':
    starter = OdooManager(14, '../enterprise')
    starter.init()
