import docker_tools as dt


class DatabaseManager(object):

    def __init__(self, version=14, odoo_db='odoo_14', docker_manager=None):
        self.version = version
        self.odoo_version = '%s.0' % version
        self.odoo_db = odoo_db
        self.docker_manager = docker_manager or dt.DockerManager(version, self.odoo_db)
        self.host = self.docker_manager.get_postgres_ip()
        self.connection = None

    def connect(self, database="template1", user="odoo", pwd="odoo"):
        if not self.host:
            self.connection = None
        connection = psycopg2.connect(
            host=self.host,
            database=database,
            user=user,
            password=pwd)
        if connection:
            self.connection = connection


    def get_databse_list(self):
        cur = self.connection.cursor()
        query = '''
        select datname from pg_database 
        where datdba=(select usesysid from pg_user where usename=current_user) 
        and not datistemplate and datallowconn
        and datname not ilike 'template%'  and datname not in ('postgres')
        order by datname
        '''
        cur.execute(query)
        rows = cur.fetchall()

        return rows

    def get_database_version(self, database_name):
        connection = psycopg2.connect(host=self.host, database=database_name)
        cur = connection.cursor()
        try:
            cur.execute("SELECT latest_version FROM ir_module_module WHERE name=%s", ('base',))
            base_version = cur.fetchone()
            return base_version
        except Exception as e:
            return 0




if __name__ == "__main__":
    import psycopg2
    db_manager = DatabaseManager()
    db_manager.connect()
    db_manager.get_databse_list()

