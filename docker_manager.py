# Copyright (C) 2024 - Michel Perrocheau (https://github.com/myrrkel).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/algpl.html).
import docker
import os
import shutil
import subprocess

GITHUB_ADDONS_DIR = 'github_addons'
DEFAULT_PORT = 8069


class DockerManager(object):
    current_process = None

    def __init__(self, version=14, odoo_db='odoo_14', stdout_signal=None):
        self.version = version
        self.odoo_version = '%s.0' % version
        self.odoo_db = odoo_db
        try:
            self.client = docker.from_env()
        except Exception as err:
            print('Impossible to start Docker client.\nError: %s' % err)
            self.client = False
            pass

        self.stdout_signal = stdout_signal

        self.network = 'odoo_one_default'
        networks = self.get_networks()
        if networks:
            self.network = networks[0].name
        else:
            self.create_network(self.network)


    def _check_client(func):
        def wrapper(self, *args, **kwargs):
            if not self.client:
                return
            return func(self, *args, **kwargs)
        return wrapper

    def print_stdout(self, msg):
        if self.stdout_signal:
            self.stdout_signal.emit(msg)
        else:
            print(msg)

    @_check_client
    def get_odoo_ip(self):
        containers = self.get_odoo_containers()
        for container in containers:
            ip = container.attrs['NetworkSettings']['Networks'][self.network]['IPAddress']
            return ip

    @_check_client
    def get_postgres_ip(self):
        containers = self.get_postgres_containers()
        for container in containers:
            ip = container.attrs['NetworkSettings']['Networks'][self.network]['Gateway']
            return ip

    @_check_client
    def odoo_database_exists(self):
        containers = self.get_postgres_containers()
        for container in containers:
            cmd = 'psql -U odoo -tAc "SELECT 1 FROM pg_database WHERE datname=\'%s\'" template1'
            cmd_res = container.exec_run(cmd % self.odoo_db)
            return bool(cmd_res.output)

    @_check_client
    def sql_execute(self, query):
        containers = self.get_postgres_containers()
        for container in containers:
            cmd_res = container.exec_run(query)
            return cmd_res.output

    @_check_client
    def create_empty_database(self):
        containers = self.get_postgres_containers()
        for container in containers:
            cmd_res = container.exec_run('createdb -h 127.0.0.1 -U odoo \'%s\'' % self.odoo_db)
            return bool(cmd_res.output)

    @_check_client
    def drop_database(self):
        containers = self.get_postgres_containers()
        for container in containers:
            cmd_res = container.exec_run('dropdb -f -h 127.0.0.1 -U odoo \'%s\'' % self.odoo_db)
            return bool(cmd_res.output)

    def get_containers(self, name='', image=''):
        if name:
            return self.client.containers.list(filters={'name': name})
        elif image:
            return self.client.containers.list(filters={'ancestor': image})

    @_check_client
    def get_networks(self):
        try:
            networks = self.client.networks.list()
        except AttributeError:
            self.create_network(self.network)
            return []

        return list(filter(lambda n: n.name not in ['none', 'bridge', 'host'], networks))

    @_check_client
    def get_postgres_containers(self):
        return self.get_containers(name='postgres')

    @_check_client
    def get_odoo_containers(self):
        return self.get_containers(name='odoo_one')

    @_check_client
    def get_odoo_running_version(self):
        for container in self.get_odoo_containers():
            return container.image.tags[0].split(':')[1]

    @_check_client
    def get_odoo_logs(self):
        for container in self.get_odoo_containers():
            try:
                return container.logs().decode()
            except Exception as err:
                pass
                return ''

    @_check_client
    def stop_odoo_containers(self):
        containers = self.get_odoo_containers()
        for container in containers:
            container.stop()

    @_check_client
    def restart_postgres(self):
        for container in self.get_postgres_containers():
            container.restart()

    @_check_client
    def pull_images(self):
        try:
            self.client.images.pull('odoo:%s' % self.odoo_version)
        except Exception as e:
            print(e)
            pass

    def get_odoo_volumes(self, path_list, version, enterprise_path):
        if path_list is None:
            path_list = []
        volumes = ['./odoo.conf:/etc/odoo/odoo.conf']
        if version == '8':
            volumes.append('odoo - db - socket: / var / run / postgresql')
        volumes.append('odoo_data{version}:/var/lib/odoo'.format(version=version))
        volumes.extend(['./'+path+':/opt/'+path for path in path_list])
        if enterprise_path:
            volumes.append(enterprise_path+':/opt/enterprise')

        volume_list = [' ' * 6 + '- ' + volume for volume in volumes]
        return '\n'.join(volume_list)

    @_check_client
    def get_db_container_name(self):
        db_containers = self.get_postgres_containers()
        return db_containers and db_containers[0].name or 'db'

    @_check_client
    def get_db_network(self):
        db_containers = self.get_postgres_containers()
        networks = db_containers and db_containers[0].attrs['NetworkSettings']['Networks']
        return networks and list(networks)[0]

    @_check_client
    def get_db_container_image(self):
        db_containers = self.get_postgres_containers()
        return db_containers and db_containers[0].image.tags[0] or 'postgres:12.4'

    def create_docker_file(self, version, external_dependencies):
        if not os.path.isdir(GITHUB_ADDONS_DIR):
            os.mkdir(GITHUB_ADDONS_DIR)
        docker_file = f'FROM odoo:{version}.0'
        docker_file += '\nUSER root'
        docker_file += f'\nCOPY ./{GITHUB_ADDONS_DIR}/ /opt/{GITHUB_ADDONS_DIR}/'
        docker_file += f'\nRUN find /opt/{GITHUB_ADDONS_DIR}/ -type f -name "requirements.txt" -exec pip install -r ''{}'' \\;'
        for addon_dependency in external_dependencies:
            external_dependency = addon_dependency.get('python', [])
            for python_dependency in external_dependency:
                docker_file = '\n'.join([docker_file, f'RUN pip install {python_dependency}'])
        docker_file += '\nUSER odoo'
        f = open("Dockerfile", "w+")
        f.write(docker_file)
        f.close()

    def create_compose_file(self, path_list=None, version='14', cmd_params="", enterprise_path=""):

        if int(version) >= 10:
            cmd = 'odoo'
        elif int(version) == 8:
            cmd = 'odoo.py'
        else:
            cmd = 'openerp-server'

        odoo_volumes = self.get_odoo_volumes(path_list, version, enterprise_path)
        db_image = self.get_db_container_image()
        db_container = self.get_db_container_name()
        db_network = self.get_db_network()
        depends = ''
        if db_container == 'db':
            depends = """    depends_on:
      - {db_container}""".format(db_container=db_image)

        db_service = self.get_compose_db_service(version) if not db_network else ''

        compose = """services:
  web:
    image: odoo_one_extra:{version}.0
    build: ./
{depends}
    ports:
      - "{port}:{port}"
    expose:
      - {port}
    command: {cmd} {cmd_params}
    volumes:
{odoo_volumes}
{db_service}
      
volumes:
  odoo_data{version}:
  postgresql_data:
  odoo-db-socket:  # For Odoo 8 only
networks:
  default:
    name: {network}
    external: true
    """
        compose = compose.format(odoo_volumes=odoo_volumes,
                                 version=version,
                                 cmd=cmd,
                                 cmd_params=cmd_params,
                                 network=db_network or self.network,
                                 depends=depends,
                                 db_service=db_service,
                                 port=DEFAULT_PORT,
                                 )
        f = open("docker-compose.yml", "w+")
        f.write(compose)
        f.close()

    def get_compose_db_service(self, version):
        db_container = self.get_db_container_name()
        if not db_container:
            return ''
        db_image = self.get_db_container_image()
        volumes = ['postgresql_data:/var/lib/postgresql/data']
        if version == '8':
            volumes.append('odoo-db-socket:/var/run/postgresql')
        db_volumes = '\n'.join([' ' * 6 + '- ' + volume for volume in volumes])
        return """
  {db_container}:
    image: {db_image}
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_PASSWORD=odoo
      - POSTGRES_USER=odoo
    ports:
      - '5432:5432'
    volumes:
{db_volumes}
""".format(db_container=db_container,
           db_volumes=db_volumes,
           db_image=db_image)

    def subprocess_run(self, params):
        self.current_process = subprocess.run(params, shell=False, capture_output=True, text=True)

    def start_compose(self):
        self.subprocess_run(['docker', 'compose', 'build'])
        # self.subprocess_run(['docker', 'build', '.', '-t', 'odoo_one_extra:16'])
        self.subprocess_run(['docker', 'compose', 'up', '-d'])

    def stop_compose(self):
        self.subprocess_run(['docker', 'compose', 'down'])

    def create_network(self, name):
        self.subprocess_run(['docker', 'network', 'create', name, '--subnet=172.19.0.0/16'])

    def docker_exists(self):
        docker_path = shutil.which("docker")
        return docker_path is not None
