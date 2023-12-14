import logging
import os
import install_docker
import docker_manager
import odoo_conf as oconf
import odoo_rpc
import subprocess
from github_modules import GithubModules

logger = logging.getLogger(__name__)


def version_to_number(version):
    return str(version).replace('.0', '')


def number_to_version(number_version):
    return '%s.0' % number_version


class OdooManager(object):

    def __init__(self, version=False, enterprise_path="", stdout_signal=None, main_window=None):
        self.version = version or self.get_last_version()
        self.enterprise_path = enterprise_path
        self.local_user = os.environ.get("USER")
        self.odoo_version = '%s.0' % self.version
        self.odoo_db = "odoo_%s" % self.version
        if self.enterprise_path:
            self.odoo_db += '_ee'
        self.docker_manager = docker_manager.DockerManager(self.version, self.odoo_db, stdout_signal)
        self.stdout_signal = stdout_signal
        self.main_window = main_window
        self.gh_modules = GithubModules(odoo=self)
        self.gh_modules.stdout_signal = stdout_signal
        self.gh_modules.print_stdout = self.print_stdout
        self.gh_modules.load(self.version, clone=True)

    def get_last_version(self):
        return 17

    def get_all_versions(self):
        return ['%0.1f' % v for v in range(8, self.get_last_version() + 1).__reversed__()]

    def set_version(self, version=''):
        self.version = int(version)
        self.odoo_version = number_to_version(self.version)

    def start_sudo(self):
        print('Docker need sudo to be installed.')

    def open_odoo_firefox(self, url):
        process = subprocess.call(['firefox', url],
                                  stdout=subprocess.PIPE, universal_newlines=True)

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

    def init(self, pull=False, open_in_browser=False):
        self.print_stdout('Start Odoo...')
        if not self.docker_manager.docker_exists():
            if self.local_user != 'root':
                self.start_sudo()
                return False
            install_docker.install_docker()
            install_docker.add_users_in_docker_group()

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
                self.open_odoo_firefox(self.odoo_start_url())
        except Exception as err:
            logger.error(err)
            pass

    def odoo_ip(self):
        return self.docker_manager.get_odoo_ip()

    def odoo_base_url(self):
        ip = self.odoo_ip()
        if not ip:
            logger.info('Restarting Odoo Server...')
            self.init()
            return self.odoo_base_url()

        return "%s:%s/web" % (ip, docker_manager.DEFAULT_PORT)

    def odoo_start_url(self):
        return "%s?db=%s" % (self.odoo_base_url(), self.odoo_db)

    def get_odoo_rpc(self):
        return odoo_rpc.OdooRpc(self.odoo_ip(),
                                docker_manager.DEFAULT_PORT,
                                self.odoo_db,
                                "admin",
                                "admin",
                                self.version)

    def check_running_version(self):
        return self.docker_manager.get_odoo_running_version() == number_to_version(self.version)

    def wait_odoo(self):
        orpc = self.get_odoo_rpc()
        admin = orpc.read('res.users', 1)
        orpc.update_addons_list()
        for addon in self.gh_modules.addons:
            orpc.install_addon(addon)

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
