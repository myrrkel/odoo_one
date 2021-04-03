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


def create_compose_file(path_list=None, version='14', cmd_params="", enterprise_path=""):

    if int(version) >= 10:
        cmd = 'odoo'
    elif int(version) == 8:
        cmd = 'odoo.py'
    else:
        cmd = 'openerp-server'
    if path_list is None:
        path_list = []
    volume_list = ['      - ./'+path+':/opt/'+path for path in path_list]
    if enterprise_path:
        volume_list.append('      - '+enterprise_path+':/opt/enterprise')
    addons_volumes = '\n'.join(volume_list)
    compose = """version: '2'
services:
  web:
    image: odoo:{version}.0
    depends_on:
      - db
    ports:
      - "8069:8069"
    expose:
      - 8069
    command: {cmd} {cmd_params}
    volumes:
      - odoo_data{version}:/var/lib/odoo
      - ./odoo.conf:/etc/odoo/odoo.conf
      - odoo-db-socket:/var/run/postgresql # For Odoo 8.0 only
{addons_volumes}
  db:
    image: postgres:10
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_PASSWORD=odoo
      - POSTGRES_USER=odoo
    ports:
      - '5432:5432'

    volumes:
      - postgresql_data:/var/lib/postgresql/data
      - odoo-db-socket:/var/run/postgresql # For Odoo 8.0 only
      
volumes:
  odoo_data{version}:
  postgresql_data:
  odoo-db-socket:  # For Odoo 8 only
networks:
  default:
    external:
      name: odoo_one_default

"""
    compose = compose.format(addons_volumes=addons_volumes,
                             version=version,
                             cmd=cmd,
                             cmd_params=cmd_params,
                             )
    f = open("docker-compose.yml", "w+")
    f.write(compose)
    f.close()


def start_compose():
    create_network()
    process = subprocess.run(['docker-compose', 'down'],
                             stdout=subprocess.PIPE, universal_newlines=True)
    process = subprocess.run(['docker-compose', 'up', '-d'],
                             stdout=subprocess.PIPE, universal_newlines=True)


def create_network():
    process = subprocess.run(['docker', 'network', 'create', 'odoo_one_default', '--subnet=172.19.0.0/16'],
                             stdout=subprocess.PIPE, universal_newlines=True)
