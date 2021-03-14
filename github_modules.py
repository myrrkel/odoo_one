from github import Github, GithubException, RateLimitExceededException
import json
import time
import subprocess
import os
import re

FILE_NAME = 'github_modules'


def strip_comments(code):
    code = str(code)
    return re.sub(r'(?m)^ *#.*\n?', '', code)

def get_json_file_name(name, version):
    return version and "%s_%s.json" % (name, version.replace('.0', '')) or "%s.json" % name


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


class GithubModules:
    version = ""
    github_modules = {}
    repositories = {}

    def __init__(self, access_token=""):

        self.github = Github(access_token)
        # For a higher rate limit, provide an access_token:
        # https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token

    def load(self, version):
        self.version = version
        self.github_modules = load_github_modules(self.version)
        self.repositories = load_repositories(self.version)
        self.clone_github_repositories()

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
        manifest_file = [d for d in files if d.type == 'file' and d.name == '__manifest__.py']
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
            print('"%s";"%s";"%s";"%s"' % (
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

    def generate_json_file(self, version=""):
        branch_ref = version or ""
        oca_modules_dict = {}
        github_users = ['OCA', 'myrrkel']
        for github_user in github_users:
            repositories = {}

            self.wait_for_rate_limit()
            for repo in self.github.get_user(github_user).get_repos():
                if repo.name.startswith('l10n') and repo.name != 'l10n-france':
                    continue

                repository_dict = self.get_repository_dict(repo, branch_ref)
                if repository_dict:
                    repositories[repo.name] = repository_dict

            oca_modules_dict[github_user] = {'repositories': repositories}

        write_json_file(FILE_NAME, version, oca_modules_dict)

    def generate_all_json_file(self):
        versions = ['11.0', '12.0', '13.0', '14.0']
        for version in versions:
            self.generate_json_file(version)

    def clone_github_repositories(self):
        if not os.path.isdir('github_addons'):
            os.mkdir('github_addons')
        for repo in self.repositories:
            github_user_path = 'github_addons/%s' % repo['github_user']
            if not os.path.isdir(github_user_path):
                os.mkdir(github_user_path)
            repo_dict = self.github_modules[repo['github_user']]['repositories'][repo['name']]
            self.git_clone(repo_dict['html_url'], github_user_path)

    def git_clone(self, html_url, github_user_path):
        repo_name = html_url.split('/')[-1].split('.')[0]
        if not os.path.isdir(repo_name):
            process = subprocess.run(['git', 'clone', html_url], cwd='./'+github_user_path,
                             stdout=subprocess.PIPE, universal_newlines=True)

    def git_pull(self, html_url, github_user_path):
        repo_name = html_url.split('/')[-1].split('.')[0]
        repo_path = '/'.join(github_user_path, repo_name)
        if os.path.isdir(repo_name):
            process = subprocess.run(['git', 'pull', '--rebase'], cwd='./'+repo_path,
                             stdout=subprocess.PIPE, universal_newlines=True)


if __name__ == '__main__':
    g = GithubModules("")

    g.generate_all_json_file()
