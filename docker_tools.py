import docker
import shutil
import subprocess
import io
import install_docker

class DockerManager(object):

    def __init__(self, version=14, odoo_db='odoo_14'):
        self.version = version
        self.odoo_version = '%s.0' % version
        self.odoo_db = odoo_db

        self.client = docker.from_env()

        self.network = 'odoo_one_default'
        networks = self.get_networks()
        if networks:
            self.network = networks[0].name
        else:
            create_network(self.network)

    def get_odoo_ip(self):
        containers = self.get_odoo_containers()
        for container in containers:
            ip = container.attrs['NetworkSettings']['Networks'][self.network]['Gateway']
            return ip

    def get_postgres_ip(self):
        containers = self.get_postgres_containers()
        for container in containers:
            ip = container.attrs['NetworkSettings']['Networks'][self.network]['Gateway']
            return ip

    def odoo_database_exists(self):
        containers = self.get_postgres_containers()
        for container in containers:
            cmd = 'psql -U odoo -tAc "SELECT 1 FROM pg_database WHERE datname=\'%s\'" template1'
            cmd_res = container.exec_run(cmd % self.odoo_db)
            return bool(cmd_res.output)

    def sql_execute(self, query):
        containers = self.get_postgres_containers()
        for container in containers:
            cmd_res = container.exec_run(query)
            return cmd_res.output

    def create_empty_database(self):
        containers = self.get_postgres_containers()
        for container in containers:
            cmd_res = container.exec_run('createdb -h 127.0.0.1 -U odoo \'%s\'' % self.odoo_db)
            return bool(cmd_res.output)

    def get_containers(self, ancestor):
        return self.client.containers.list(filters={'ancestor': ancestor})

    def get_networks(self):
        try:
            networks = self.client.networks.list()
        except AttributeError:
            create_network(self.network)
            return []

        return list(filter(lambda n: n.name not in ['none', 'bridge', 'host'], networks))

    def get_postgres_containers(self):
        return self.get_containers('postgres:10')

    def get_odoo_containers(self):
        return self.get_containers('odoo:%s' % self.odoo_version)

    def stop_odoo_containers(self):
        containers = self.get_odoo_containers()
        for container in containers:
            container.stop()

    def restart_postgres(self):
        for container in self.get_postgres_containers():
            container.restart()

    def pull_images(self):
        try:
            self.client.images.pull('odoo:%s' % self.odoo_version)
        except Exception as e:
            print(e)
            pass


def create_compose_file(path_list=None, version='14', cmd_params="", enterprise_path="", network=""):

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
      name: {network}

"""
    compose = compose.format(addons_volumes=addons_volumes,
                             version=version,
                             cmd=cmd,
                             cmd_params=cmd_params,
                             network=network,
                             )
    f = open("docker-compose.yml", "w+")
    f.write(compose)
    f.close()


def restart_docker():
    process = subprocess.Popen(['service', 'docker', 'restart'],
                             stdout=subprocess.PIPE, shell=False)


def docker_exists():
    docker_path = shutil.which("docker")
    return docker_path is not None


def compose_exists():
    compose_path = shutil.which("docker-compose")
    return compose_path is not None


def start_compose():

    process = subprocess.run(['docker-compose', 'up', '-d'],
                             stdout=subprocess.PIPE, shell=False)


def stop_compose():
    process = subprocess.run(['docker-compose', 'down'],
                             stdout=subprocess.PIPE, universal_newlines=True)
    if process:
        print('stop')


def create_network(name):
    process = subprocess.run(['docker', 'network', 'create', name, '--subnet=172.19.0.0/16'],
                             stdout=subprocess.PIPE, universal_newlines=True)
