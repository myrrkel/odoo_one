from github import Github, GithubException, RateLimitExceededException
import json
import logging
import os
import re
import settings
import subprocess
import time
import odoo_manager

logger = logging.getLogger(__name__)

FILE_NAME = 'github_modules'
DATA_DIR = './data/'
GITHUB_ADDONS_DIR = 'github_addons'


def strip_comments(code):
    code = str(code)
    return re.sub(r'(?m)^ *#.*\n?', '', code)


def get_json_file_name(name, version):
    file_name = version and "%s_%s.json" % (name, version.replace('.0', '')) or "%s.json" % name
    return DATA_DIR + file_name


def load_json(name, version):
    try:
        return json.load(open(get_json_file_name(name, version), "r"))
    except Exception as e:
        return {}


def load_github_modules(version):
    return load_json(FILE_NAME, version)


def load_repositories(version):
    return load_json('repositories', version)


def write_json_file(name, version, vals):
    res_file = open(get_json_file_name(name, version), "w")
    res_file.write(json.dumps(vals, sort_keys=True, indent=4))
    res_file.close()


def write_repositories(version, repositories):
    write_json_file('repositories', version, repositories)


def print_version_abstract(number_version):
    users = load_github_modules(number_version)
    print('Version: %s' % number_version)
    for user in users:
        modules = []
        print('User: %s' % user)
        repositories = list(users[user]['repositories'].keys())
        repositories = [r for r in repositories if r not in ['OpenUpgrade']
                        and (not r.startswith('l10n-') or r == 'l10n-france')]
        print('Repositories: %s' % repositories)
        print('Count repositories: %s' % len(repositories))
        for repository in repositories:
            modules.extend(users[user]['repositories'][repository]['modules'])

        print('Modules: %s' % modules)
        print('Count modules: %s' % len(modules))


class GithubModules:
    version = ""
    odoo_version = ""
    github_modules = []
    github_repositories = {}
    repositories = {}
    addons = []
    modules = []
    addons_path_list = []
    external_dependencies = []
    github_users = ['OCA', 'myrrkel']
    db_settings = {'modules': []}
    access_token = ""
    github = Github()
    stdout_signal = None
    print_stdout = None
    log = ''
    need_refresh = True
    need_clone = False

    def __init__(self, access_token="", odoo=None):
        if odoo:
            self.odoo = odoo
        else:
            self.odoo = odoo_manager.OdooManager()
        last_version = self.odoo.get_last_version()
        all_versions = self.odoo.get_all_versions()

        if access_token:
            self.access_token = access_token
        self.init_github()
        # For a higher rate limit, provide an access_token:
        # https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token

    def init_github(self):
        self.github = Github(self.access_token)

    def set_version(self, odoo_version):
        previous_version = self.version
        self.version = odoo_manager.version_to_number(odoo_version)
        self.odoo_version = odoo_manager.number_to_version(self.version)
        if self.version != previous_version:
            self.need_refresh = True

    def load(self, odoo_version, clone=False, force_refresh=False):
        self.addons = []
        self.set_version(odoo_version)
        self.load_database_settings()
        self._compute_addons_repositories()
        if self.need_refresh or force_refresh:
            self.github_modules = load_github_modules(self.version)
            self._compute_github_repositories()
            if self.need_clone or clone:
                self.clone_github_repositories(self.odoo_version)
            self.need_refresh = False

    def _compute_addons_repositories(self):
        if not self.db_settings:
            return
        self.addons = []
        self.external_dependencies = []
        self.modules = self.db_settings['modules']
        self.repositories = {}
        for module in self.modules:
            self.addons.append(module['name'])
            repository = self.find_repository(module['repository'], module['user'])
            if not repository:
                repository = {'name': module['repository'], 'user': module['user']}
                self.repositories[module['repository']] = repository
                self.need_refresh = True

            try:
                self._compute_external_dependencies(module)
            except Exception as err:
                self.logger(str(err))
                pass

    def _compute_external_dependencies(self, module):
        manifest = self.get_local_module_manifest(module['user'],
                                                  module['repository'],
                                                  self.odoo_version, module['name'])
        external_dependency = manifest.get('external_dependencies', False)
        if external_dependency:
            self.external_dependencies.append(external_dependency)

    def _compute_github_repositories(self):
        for user in self.github_modules.keys():
            for repository_name in self.github_modules[user]['repositories'].keys():
                repository = {'user': user}
                repository['name'] = repository_name
                self.github_repositories[repository_name] = repository

    def find_repository(self, repository, user):
        if repository in self.repositories:
            if self.repositories[repository].get('user') == user:
                return self.repositories[repository]
        return False

    def add_addon_db_settings(self, addon, user, repository, db_name=''):
        if not self.db_settings:
            self.db_settings = {'modules': []}
        self.db_settings['modules'].append({'name': addon, 'user': user, 'repository': repository})
        self.save_database_settings(db_name)

    def remove_addon_db_settings(self, addon, db_name=''):
        for module in self.db_settings['modules']:
            if module['name'] == addon:
                self.db_settings['modules'].remove(module)

        self.save_database_settings(db_name)

    def load_database_settings(self, db_name=''):
        self.db_settings = settings.get_setting('github modules %s' % (db_name or 'odoo_%s' % self.version))
#        if not self.db_settings:
#            self.db_settings = {'modules': [{'name': 'web_environment_ribbon', 'user': 'OCA', 'repository': 'web'}]}

    def save_database_settings(self, db_name=''):
        setting_name = 'github modules %s' % (db_name or 'odoo_%s' % self.version)
        settings.save_setting(setting_name, self.db_settings)

    def check_github_rate_limit(self):
        rate_limit = self.github.get_rate_limit()
        if rate_limit.core.remaining < 100:
            print("Rate limit is to low: %s" % rate_limit.core.remaining)
            return False
        return True

    def wait_for_rate_limit(self):
        while not self.check_github_rate_limit():
            time.sleep(60)

    def get_dir_contents(self, repo, path, ref=''):
        try:
            return repo.get_contents(path, ref)
        except RateLimitExceededException:
            self.wait_for_rate_limit()
            return self.get_dir_contents(repo, path, ref)
        except GithubException as e:
            if 'No commit found for the ref' not in e.data.get('message', False):
                print(e)
        return []

    def get_manifest_name(self, branch_ref):
        if branch_ref in ['8.0', '9.0']:
            return '__openerp__.py'
        else:
            return '__manifest__.py'

    def get_local_module_manifest(self, user_name, repo_name, branch_ref, module_name):
        manifest_name = self.get_manifest_name(branch_ref)
        manifest_file = os.path.join(GITHUB_ADDONS_DIR, user_name, repo_name, module_name, manifest_name)
        with open(manifest_file) as f:
            manifest = f.read()
            return eval(manifest)

    def get_github_module_manifest(self, repo, branch_ref, module_name):
        files = self.get_dir_contents(repo, './%s' % module_name, ref=branch_ref)
        manifest_name = self.get_manifest_name(branch_ref)
        manifest_file = [d for d in files if d.type == 'file' and d.name == manifest_name]
        if manifest_file:
            try:
                manifest = eval(strip_comments(manifest_file[0].decoded_content.decode('UTF-8')))
                module_dict = {'name': module_name,
                               'display_name': manifest.get('name', ''),
                               'summary': manifest.get('summary', ''),
                               'version': manifest.get('version', ''),
                               'author': manifest.get('author', ''),
                               'category': manifest.get('category', ''),
                               }
                return module_dict
            except RateLimitExceededException:
                self.wait_for_rate_limit()
                return self.get_github_module_manifest(repo, branch_ref, module_name)
        return {}

    def get_repository_dict(self, repo, branch_ref):
        modules = {}
        dirs = [d for d in self.get_dir_contents(repo, '.', ref=branch_ref) if d.type == 'dir' and d.name != 'setup']
        if dirs:
            self.logger('"%s";"%s";"%s";"%s"' % (
                repo.name, repo.description, repo.html_url, repo.default_branch))
            for sub_dir in dirs:
                module_dict = self.get_github_module_manifest(repo, branch_ref, sub_dir.name)
                if module_dict:
                    modules[sub_dir.name] = module_dict
        if modules:
            repo_dict = {'name': repo.name, 'description': repo.description, 'html_url': repo.html_url,
                         'default_branch': repo.default_branch, 'modules': modules}
            return repo_dict
        return {}

    def get_repository_module_list(self, repo, branch_ref):
        modules = []
        dirs = [d for d in self.get_dir_contents(repo, '.', ref=branch_ref) if d.type == 'dir' and d.name != 'setup']
        if dirs:
            for sub_dir in dirs:
                module_dict = self.get_github_module_manifest(repo, branch_ref, sub_dir.name)
                modules.append(module_dict)
        return modules

    def generate_mini_json_file(self, version=""):
        branch_ref = version or ""
        oca_modules_list = []
        for github_user in self.github_users:
            self.wait_for_rate_limit()
            for repo in self.github.get_user(github_user).get_repos():
                oca_modules_list.extend(self.get_repository_module_list(repo, branch_ref))
        write_json_file('mini_%s' % FILE_NAME, version, oca_modules_list)

    def generate_json_file(self, version=""):
        branch_ref = version or ""
        oca_modules_dict = {}

        for github_user in self.github_users:
            repositories = {}
            self.wait_for_rate_limit()
            for repo in self.github.get_user(github_user).get_repos():
                repository_dict = self.get_repository_dict(repo, branch_ref)
                if repository_dict:
                    repositories[repo.name] = repository_dict

            oca_modules_dict[github_user] = {'repositories': repositories}

        write_json_file(FILE_NAME, version, oca_modules_dict)

    def generate_all_json_file(self):
        for version in self.odoo.get_all_versions():
            self.generate_json_file(version)

    def generate_all_github_modules_file(self):
        modules = []
        for v in self.odoo.get_all_versions():
            users = load_github_modules(v)
            for user in users:
                for repo in users[user]['repositories']:
                    for module_name in users[user]['repositories'][repo]['modules']:
                        module = users[user]['repositories'][repo]['modules'][module_name]
                        module_founds = [m for m in modules if m['name'] == module_name]
                        if module_founds:
                            module_founds[0]['versions'].append(v)
                        else:
                            module['versions'] = [v]
                            module.pop('version')
                            module['repository'] = repo
                            module['user'] = user
                            modules.append(module)

        write_json_file('github_modules', 'all', modules)

    def clone_github_repositories(self, version):
        self.addons_path_list = []
        if not os.path.isdir(GITHUB_ADDONS_DIR):
            os.mkdir(GITHUB_ADDONS_DIR)
        for repository in self.repositories:
            self.clone_github_repository(self.repositories[repository], version)

    def clone_github_repository(self, repository, version):
        github_user_path = os.path.join(GITHUB_ADDONS_DIR, repository['user'])
        if not os.path.isdir(github_user_path):
            os.mkdir(github_user_path)
        if repository.get('url', False):
            url = repository['url']
        else:
            try:
                repo_dict = self.github_modules[repository['user']]['repositories'][repository['name']]
                url = repo_dict['html_url']
            except Exception as e:
                print(e)
                self.need_clone = True
                return

        repo_name = url.split('/')[-1].split('.')[0]
        self.git_clone(url, github_user_path, repo_name)
        self.git_checkout(github_user_path, repo_name, version)
        self.addons_path_list.append(github_user_path + "/" + repo_name)

    def git_clone(self, url, github_user_path, repo_name):
        path = github_user_path + "/" + repo_name
        if not os.path.isdir(path):
            process = subprocess.run(['git', 'clone', url], cwd='./' + github_user_path,
                                     stdout=subprocess.PIPE, universal_newlines=True)

    def git_checkout(self, github_user_path, repo_name, version):
        path = github_user_path + "/" + repo_name
        if os.path.isdir(path):
            process = subprocess.run(['git', 'checkout', version], cwd='./' + path,
                                     stdout=subprocess.PIPE, universal_newlines=True)

    def git_checkout_enterprise(self, version, enterprise_path):
        process = subprocess.run(['git', 'checkout', version], cwd='./' + enterprise_path,
                                 stdout=subprocess.PIPE, universal_newlines=True)

    def git_pull(self, html_url, github_user_path):
        repo_name = html_url.split('/')[-1].split('.')[0]
        repo_path = '/'.join(github_user_path, repo_name, repo_name)
        if os.path.isdir(repo_name):
            process = subprocess.run(['git', 'pull', '--rebase'], cwd='./' + repo_path,
                                     stdout=subprocess.PIPE, universal_newlines=True)

    def logger(self, text):
        self.log = '\n'.join([self.log, text]) if self.log else text
        if self.stdout_signal:
            self.print_stdout(self.log)
        print(text)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        credential = sys.argv[1]
    else:
        logger.error("A Github credential is required.")
        sys.exit(2)
    gh_modules = GithubModules(credential)
    g = GithubModules(credential)
    versions = gh_modules.odoo.get_all_versions()

    if len(sys.argv) == 4:
        if sys.argv[2] == '-v':
            if sys.argv[3] == 'all':
                pass
            else:
                versions = [sys.argv[3]]
        elif sys.argv[2] == '-n':
            versions = versions[:int(sys.argv[3])]
        else:
            logger.error("unknown parameter")
            sys.exit(2)
    else:
        versions = versions[:1]

    for v in versions:
        g.generate_json_file(v)
    gh_modules.generate_all_github_modules_file()

    for v in versions:
        print_version_abstract(odoo_manager.version_to_number(v))
