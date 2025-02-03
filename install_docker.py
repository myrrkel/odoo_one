# Copyright (C) 2024 - Michel Perrocheau (https://github.com/myrrkel).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/algpl.html).
import os
import subprocess
import shutil

# Run this script with sudo to install docker


def install_docker():

    process = subprocess.run(['apt-get', 'install', 'curl'],
                             stdout=subprocess.PIPE, universal_newlines=True)

    process = subprocess.run(['curl', '-fsSL', 'https://get.docker.com', '-o', 'get-docker.sh'],
                             stdout=subprocess.PIPE, universal_newlines=True)

    process = subprocess.run(['sh', 'get-docker.sh'],
                             stdout=subprocess.PIPE, universal_newlines=True)


def install_docker_windows():
    url = 'https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe?utm_source=docker&utm_medium=webreferral&utm_campaign=docs-driven-download-win-amd64'
    process = subprocess.run(['powershell', 'Invoke-WebRequest', '-Uri', url, '-OutFile', 'docker.exe'],
                             stdout=subprocess.PIPE, universal_newlines=True)
    process = subprocess.run(['powershell', 'Start-Process', '-FilePath', 'docker.exe', '-ArgumentList', '/install', '-Wait', '-PassThru'],
                             stdout=subprocess.PIPE, universal_newlines=True)

def install_docker_mac():
    url = 'https://desktop.docker.com/mac/main/arm64/Docker.dmg?utm_source=docker&utm_medium=webreferral&utm_campaign=docs-driven-download-mac-arm64'
    process = subprocess.run(['curl', '-L', url, '-o', 'Docker.dmg'],
                             stdout=subprocess.PIPE, universal_newlines=True)
    process = subprocess.run(['hdiutil', 'attach', 'Docker.dmg'],
                             stdout=subprocess.PIPE, universal_newlines=True)
    process = subprocess.run(['sudo', 'installer', '-pkg', '/Volumes/Docker/Docker.pkg', '-target', '/'],
                             stdout=subprocess.PIPE, universal_newlines=True)
    process = subprocess.run(['hdiutil', 'detach', '/Volumes/Docker'],
                             stdout=subprocess.PIPE, universal_newlines=True)

def add_users_in_docker_group():
    process = subprocess.run(['who'], stdout=subprocess.PIPE, universal_newlines=True)
    users = process.stdout
    for user in users.split('\n'):
        user_name = user.split(' ')[0]
        if user_name:
            process = subprocess.run(['usermod', '-aG', 'docker', user_name],
                                     stdout=subprocess.PIPE, universal_newlines=True)
            process = subprocess.run(['newgrp', 'docker'],
                                     stdout=subprocess.PIPE, universal_newlines=True)
            if process.stdout:
                print(process.stdout)


if __name__ == "__main__":
    if os.name == 'nt':
        install_docker_windows()
    elif os.name == 'posix':
        install_docker()
        add_users_in_docker_group()
    elif os.name == 'mac':
        install_docker_mac()

