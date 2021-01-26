from uvicore.support.dumper import dump, dd
from uvicore.support.module import location
from uvicore.database import Connection
from uvicore.typing import Dict, List


class Db:
    """Database Service Provider Mixin"""

    #def _add_db_definition(self, key, value):
        # if type(value) == list:
        #     if not self.package.database[key]: self.package.database[key] = []
        #     self.package.database[key].extend(value)
        # elif type(value) == dict:
        #     self.package.database[key].merge(value)
        # else:
        #     self.package.database[key] = value

        #self.package.database[key] = value

        # if 'database' not in self.package:
        #     self.package.database = Dict()
        # if type(value) == list:
        #     if key not in self.package.database: self.package.database = []
        #     self.package['database'][key].extend(value)
        # else:
        #     self.package['database'][key] = value

    def connections(self, config: Dict, default: str):
        #connections = []
        for name, connection in config.items():

            # Build URL and metakey
            # Metakey cannot be the connection name.  If 2 connections share the exact
            # same database (host, port, dbname) then they need to also share the same
            # metedata for foreign keys to work properly.
            if connection.driver == 'sqlite':
                url = 'sqlite:///' + connection.database
                metakey = url
            else:
                url = (
                    connection.driver
                    + '+' + connection.dialect
                    + '://' + connection.username
                    + ':' + connection.password
                    + '@' + connection.host
                    + ':' + str(connection.port)
                    + '/' + connection.database
                )
                metakey = (
                    connection.host
                    + ':' + str(connection.port)
                    + '/' + connection.database
                )

            # Merge new values into connection SuperDict
            if not connection.prefix: connection.prefix = ''
            connection.merge({
                'name': name,
                'metakey': metakey,
                'url': url
            })
            #connections.append(connection)

        self.package.database.connections = config
        self.package.database.connection_default = default


    def connectionsORIG(self, config: Dict, default: str):
        # Here we translate a config connectoin dictionary into an actual Connection Class
        connections = []
        for name, connection in config.items():
            # Metakey cannot be the connection name.  If 2 connections share the exact
            # same database (host, port, dbname) then they need to also share the same
            # metedata for foreign keys to work properly.
            if connection.get('driver') == 'sqlite':
                url = 'sqlite:///' + connection.get('database')
                metakey = url
            else:
                url = (connection.get('driver')
                    + '+' + connection.get('dialect')
                    + '://' + connection.get('username')
                    + ':' + connection.get('password')
                    + '@' + connection.get('host')
                    + ':' + str(connection.get('port'))
                    + '/' + connection.get('database')
                )
                metakey = (connection.get('host')
                    + ':' + str(connection.get('port'))
                    + '/' + connection.get('database')
                )

            connections.append(Connection(
                name=name,
                driver=connection.get('driver'),
                dialect=connection.get('dialect'),
                host=connection.get('host'),
                port=connection.get('port'),
                database=connection.get('database'),
                username=connection.get('username'),
                password=connection.get('password'),
                prefix=connection.get('prefix') or '',
                metakey=metakey,
                url=url,
            ))
        self._add_db_definition('connections', connections)
        self._add_db_definition('connection_default', default)


    def models(self, items: List):
        # Default registration
        self.package.registers.defaults({'models': True})

        # Register models only if allowed
        if self.package.registers.models:
            self.package.database.models = items

    def tables(self, items: List):
        # Default registration
        self.package.registers.defaults({'tables': True})

        # Register tables only if allowed
        if self.package.registers.tables:
            self.package.database.tables = items

    def seeders(self, items: List):
        # Default registration
        self.package.registers.defaults({'seeders': True})

        # Register seeders only if allowed
        if self.package.registers.seeders:
            self.package.database.seeders = items