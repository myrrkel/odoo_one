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


def install_compose():

    process = subprocess.run(['apt-get', 'install', '-y', 'docker-compose'],
                             stdout=subprocess.PIPE, universal_newlines=True)


if __name__ == "__main__":
    install_docker()
    add_users_in_docker_group()
    install_compose()

