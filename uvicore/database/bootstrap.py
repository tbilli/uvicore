import uvicore
from uvicore.typing import Dict
from uvicore.events import Handler
from uvicore.support.module import load
from uvicore.support.dumper import dump, dd
from uvicore.foundation.events.app import Booted as OnAppBooted


class Database(Handler):

    def __call__(self, event: OnAppBooted):
        """Bootstrap the Database after the Application is Booted"""

        # Gather all connections, models, tables
        # No need to gather seeder classes, I get those in the ./uvicore db seed command
        connections = Dict()
        models = []; tables = []
        last_default = None; app_default = None
        for package in uvicore.app.packages.values():
            if not 'database' in package: continue

            # Get last defined default connection
            if package.database.connection_default: last_default = package.database.connection_default

            # Get running app default connection
            if package.main and package.database.connection_default: app_default = package.database.connection_default

            # Append connections
            connections.merge(package.database.connections)

            # Append models
            models.extend(package.database.models or [])

            # Append tables
            tables.extend(package.database.tables or [])

        # Initialize Database with all connections at once
        uvicore.db.init(app_default or last_default, connections)

        # Dynamically Import models, tables and seeders
        for model in models: load(model)
        for table in tables: load(table)

        # Connect to all databases one time, after the system has started up
        @uvicore.events.handle(['uvicore.console.events.command.Startup', 'uvicore.http.events.server.Startup'])
        async def uvicore_startup(event):
            # Loop each database and connect()
            # I used to do it on-the-fly in db.py but was getting pool errors
            for metakey, database in uvicore.db.databases.items():
                if not database.is_connected:
                    await database.connect()

        # Disconnect from all databases after the system has shutdown
        @uvicore.events.handle(['uvicore.console.events.command.Shutdown', 'uvicore.http.events.server.Shutdown'])
        async def uvicore_shutdown(event):
            # Disconnect from all connected databases
            await uvicore.db.disconnect(from_all=True)
