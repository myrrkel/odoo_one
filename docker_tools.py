import docker
import shutil
import subprocess


def docker_exists():
    docker_path = shutil.which("docker")
    return docker_path is not None


def compose_exists():
    compose_path = shutil.which("docker-compose")
    return compose_path is not None


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
            if process.stdout:
                print(process.stdout)


def install_compose():

    process = subprocess.run(['apt-get', 'install', '-y', 'docker-compose'],
                             stdout=subprocess.PIPE, universal_newlines=True)


def create_compose_file(path_list=[]):
    volume_list = ['      - ./'+path+':/opt/'+path for path in path_list]
    addons_volumes = '\n'.join(volume_list)
    compose = """version: '2'
services:
  web:
    image: odoo:14.0
    depends_on:
      - db
    ports:
      - "8069:8069"
    command: odoo -d odoo
    volumes:
      - ./odoo.conf:/etc/odoo/odoo.conf
{addons_volumes}
  db:
    image: postgres:10
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_PASSWORD=odoo
      - POSTGRES_USER=odoo
"""
    compose = compose.format(addons_volumes=addons_volumes)
    f = open("docker-compose.yml", "w+")
    f.write(compose)
    f.close()


def start_compose():
    process = subprocess.run(['docker-compose', 'down'],
                             stdout=subprocess.PIPE, universal_newlines=True)
    process = subprocess.run(['docker-compose', 'up', '-d'],
                             stdout=subprocess.PIPE, universal_newlines=True)
