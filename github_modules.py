from github import Github, GithubException, RateLimitExceededException
import settings
import json
import time
import subprocess
import os
import re
import odoo_manager

FILE_NAME = 'github_modules'
DATA_DIR = './data/'


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


def generate_all_github_modules_file():
    modules = []
    for v in ALL_VERSIONS:
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


def version_to_number(version):
    return str(version).replace('.0', '')


def number_to_version(number_version):
    return '%s.0' % number_version


class GithubModules:
    version = ""
    odoo_version = ""
    github_modules = []
    github_repositories = {}
    repositories = {}
    addons = []
    addons_path_list = []
    github_users = ['OCA', 'myrrkel']
    db_settings = {'modules': []}
    access_token = ""
    github = Github()
    stdout_signal = None
    print_stdout = None
    log = ''
    need_refresh = True

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
        self.version = version_to_number(odoo_version)
        self.odoo_version = number_to_version(self.version)
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
            if clone:
                self.clone_github_repositories(self.odoo_version)
            self.need_refresh = False

    def _compute_addons_repositories(self):
        if not self.db_settings:
            return
        for module in self.db_settings['modules']:
            self.addons.append(module['name'])
            repository = self.find_repository(module['repository'], module['user'])
            if not repository:
                self.repositories[module['repository']] = {'name': module['repository'], 'user': module['user']}

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

    def get_module_dict(self, repo, branch_ref, module):
        files = self.get_dir_contents(repo, './%s' % module.name, ref=branch_ref)
        if branch_ref in ['8.0', '9.0']:
            manifest_name = '__openerp__.py'
        else:
            manifest_name = '__manifest__.py'
        manifest_file = [d for d in files if d.type == 'file' and d.name == manifest_name]
        if manifest_file:
            try:
                manifest = eval(strip_comments(manifest_file[0].decoded_content.decode('UTF-8')))
                module_dict = {'name': module.name,
                               'display_name': manifest.get('name', ''),
                               'summary': manifest.get('summary', ''),
                               'version': manifest.get('version', ''),
                               'author': manifest.get('author', ''),
                               'category': manifest.get('category', ''),
                               }
                return module_dict
            except RateLimitExceededException:
                self.wait_for_rate_limit()
                return self.get_module_dict(repo, branch_ref, module)
        return {}

    def get_repository_dict(self, repo, branch_ref):
        modules = {}
        dirs = [d for d in self.get_dir_contents(repo, '.', ref=branch_ref) if d.type == 'dir' and d.name != 'setup']
        if dirs:
            self.logger('"%s";"%s";"%s";"%s"' % (
                repo.name, repo.description, repo.html_url, repo.default_branch))
            for sub_dir in dirs:
                module_dict = self.get_module_dict(repo, branch_ref, sub_dir)
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
                module_dict = self.get_module_dict(repo, branch_ref, sub_dir)
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

    def clone_github_repositories(self, version):
        self.addons_path_list = []
        if not os.path.isdir('github_addons'):
            os.mkdir('github_addons')
        for repo_name in self.repositories:
            repo = self.repositories[repo_name]
            github_user_path = 'github_addons/%s' % repo['user']
            if not os.path.isdir(github_user_path):
                os.mkdir(github_user_path)
            if repo.get('url', False):
                url = repo['url']
            else:
                try:
                    repo_dict = self.github_modules[repo['user']]['repositories'][repo['name']]
                    url = repo_dict['html_url']
                except Exception as e:
                    print(e)
                    continue

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
    generate_all_github_modules_file()

    # import sys
    # if len(sys.argv) > 1:
    #     credential = sys.argv[1]
    #     g = GithubModules(credential)
    #     # versions = ALL_VERSIONS[3:]
    #     versions = ALL_VERSIONS[:3]
    #     for v in versions:
    #         g.generate_json_file(v)
