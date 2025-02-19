# Copyright (C) 2024 - Michel Perrocheau (https://github.com/myrrkel).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/algpl.html).
try:
    from github import Github, GithubException, RateLimitExceededException
except ImportError:
    print('Please make sure Git is installed')
    class Github (object):
        def __init__(self, access_token=''):
            pass
    class GithubException (Exception):
        def __init__(self, message=''):
            self.message = message
    class RateLimitExceededException (Exception):
        def __init__(self, message=''):
            self.message = message
    pass
import argparse
from datetime import datetime
import json
import logging
import os
import re
import requests
import settings
import sys
import subprocess
import time
from tools import version_to_number, number_to_version, resource_path

logger = logging.getLogger(__name__)
logger.setLevel("INFO")
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

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
        file_path = resource_path(get_json_file_name(name, version))
        return json.load(open(file_path, "r"))
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


def get_manifest_name(branch_ref):
    if branch_ref in ['8.0', '9.0']:
        return '__openerp__.py'
    else:
        return '__manifest__.py'


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
            import odoo_manager
            self.odoo = odoo_manager.OdooManager()

        if access_token:
            self.access_token = access_token
        self.init_github()
        # For a higher rate limit, provide an access_token:
        # https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token

    def init_github(self):
        try:
            if self.access_token:
                self.github = Github(self.access_token)
        except Exception as err:
            logger.error(err, exc_info=True)
            pass

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
                repository = {'user': user, 'name': repository_name}
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

    def get_local_module_manifest(self, user_name, repo_name, branch_ref, module_name):
        manifest_name = get_manifest_name(branch_ref)
        manifest_file = os.path.join(GITHUB_ADDONS_DIR, user_name, repo_name, module_name, manifest_name)
        with open(manifest_file) as f:
            manifest = f.read()
            return eval(manifest)

    def get_github_module_manifest(self, repo, branch_ref, module_name):
        manifest_name = get_manifest_name(branch_ref)
        manifest_file = self.get_dir_contents(repo,
                                              './%s/%s' % (module_name, manifest_name),
                                              ref=branch_ref)
        if manifest_file:
            try:
                manifest = eval(strip_comments(manifest_file.decoded_content.decode('UTF-8')))
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

    def get_directory_folders(self, repo, branch_ref):
        url = repo.trees_url.replace('{/sha}', '/'+branch_ref)
        try:
            headers = {'Authorization': 'token ' + self.access_token}
            response = requests.get(url, headers=headers)
            data_json = json.loads(response.content)
            tree = data_json.get('tree')
            if not tree:
                return []
            return [d['path'] for d in tree if d['type'] == 'tree' and d['path'][0] != '.']
        except Exception as err:
            logger.error(err, exc_info=True)
            pass

    def get_repository_dict(self, repo, branch_ref):
        start_time = datetime.now()
        repo_dict = {}
        modules = {}
        self.logger('"%s";"%s";"%s"' % (repo.name, repo.description, repo.html_url))
        dirs = self.get_directory_folders(repo, branch_ref)
        if dirs:
            for sub_dir in dirs:
                if sub_dir.startswith('.') or sub_dir == 'setup':
                    continue
                module_dict = self.get_github_module_manifest(repo, branch_ref, sub_dir)
                if module_dict:
                    modules[sub_dir] = module_dict
        if modules:
            repo_dict = {'name': repo.name, 'description': repo.description, 'html_url': repo.html_url,
                         'default_branch': repo.default_branch, 'modules': modules}
        self.logger("Done in %0.2f seconds" % (datetime.now() - start_time).total_seconds())
        return repo_dict

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
        modules_list = []
        for github_user in self.github_users:
            self.wait_for_rate_limit()
            for repo in self.github.get_user(github_user).get_repos():
                modules_list.extend(self.get_repository_module_list(repo, branch_ref))
        write_json_file('mini_%s' % FILE_NAME, version, modules_list)

    def generate_json_file(self, version="", repo_to_update=None):
        if repo_to_update is None:
            repo_to_update = []
        branch_ref = version or ""
        modules_dict = load_github_modules(version)

        for github_user in self.github_users:
            repositories = {}
            self.wait_for_rate_limit()
            for repo in self.github.get_user(github_user).get_repos():
                if (repo_to_update and repo.name not in repo_to_update) or repo.name.startswith('.'):
                    continue
                repository_dict = self.get_repository_dict(repo, branch_ref)
                if repository_dict:
                    repositories[repo.name] = repository_dict

            if github_user not in modules_dict:
                modules_dict[github_user] = {'repositories': repositories}
            else:
                for repo in repositories.keys():
                    modules_dict[github_user]['repositories'][repo] = repositories[repo]

        write_json_file(FILE_NAME, version, modules_dict)

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

    def run_subprocess(self, run_list, cwd=''):
        process = subprocess.run(run_list, cwd=cwd,
                                 stdout=subprocess.PIPE, universal_newlines=True)

    def git_clone(self, url, github_user_path, repo_name):
        path = github_user_path + "/" + repo_name
        if not os.path.isdir(path):
            self.run_subprocess(['git', 'clone', url], cwd='./' + github_user_path)

    def git_checkout(self, github_user_path, repo_name, version):
        path = github_user_path + "/" + repo_name
        if os.path.isdir(path):
            self.run_subprocess(['git', 'checkout', version], cwd='./' + path)

    def git_checkout_enterprise(self, version, enterprise_path):
        self.run_subprocess(['git', 'checkout', version], cwd='./' + enterprise_path)

    def git_pull(self, github_user_path, repo_name):
        path = github_user_path + "/" + repo_name
        if not os.path.isdir(path):
            self.run_subprocess(['git', 'pull', '--rebase'], cwd='./' + path)

    def logger(self, text):
        self.log = '\n'.join([self.log, text]) if self.log else text
        if self.stdout_signal:
            self.print_stdout(self.log)
        logger.info(text)


if __name__ == '__main__':

    def create_addons_files(credential, versions, repo_to_update):
        gh_addons = GithubModules(credential)
        for v in versions:
            start_time = datetime.now()
            gh_addons.generate_json_file(v, repo_to_update)
            logger.info("File creation in %0.2f seconds" % (datetime.now() - start_time).total_seconds())
        gh_addons.generate_all_github_modules_file()
        for v in versions:
            print_version_abstract(version_to_number(v))

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--credential', dest='credential')
    parser.add_argument('-r', '--repositories', dest='repositories')
    parser.add_argument('-v', '--versions', dest='versions')
    parser.add_argument('-n', '--number', dest='number')
    try:
        args = parser.parse_args()
    except Exception as err:
        logger.error(err)
        sys.exit(2)

    gh_modules = GithubModules()
    versions = gh_modules.odoo.get_all_versions()
    repo_to_update = []
    credential = args.credential
    if not credential:
        credential = os.environ.get('GITHUB_CREDENTIAL', '')
        if not credential:
            logger.error("A Github credential is required.")
            sys.exit(2)

    if args.versions:
        if args.versions == 'all':
            pass
        else:
            versions = args.versions.split(',')
    else:
        versions = versions[:1]

    if args.number:
        versions = versions[:int(args.number)]

    if args.repositories:
        repo_to_update = args.repositories.split(',')

    create_addons_files(credential, versions, repo_to_update)
