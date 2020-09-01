import typer
from typing import Optional
from uvicore import app, db, log
from uvicore.support.click import click, group_kargs
from uvicore.support.dumper import dump, dd
from uvicore import log
from uvicore.support import module

# Commands
create = typer.Typer()
drop = typer.Typer()
recreate = typer.Typer()
seed = typer.Typer()
reseed = typer.Typer()
connections = typer.Typer()

# Common arguments
connection_arg = typer.Argument(..., help='Connection(s) name (comma separated for multiples)')

def get_metakeys(connections: str):
    """Convert connections into deduplicated metakeys"""
    metakeys = []
    connections = connections.split(',') if ',' in connections else [connections]
    for connection in connections:
        conn = db.connection(connection)
        if conn:
            metakey = conn.metakey
            if metakey not in metakeys:
                metakeys.append(metakey)
        else:
            exit('Connection string {} not found in configs'.format(connection))
    return metakeys

@create.command()
def create_cmd(connections: str = connection_arg):
    """Create tables for connection(s)"""
    #log.header('Creating tables for connections: [' + connections + ']')
    metakeys = get_metakeys(connections)
    for metakey in metakeys:
        log.header('Creating tables in {} in topologically order'.format(metakey))
        metadata = db.metadata(metakey=metakey)
        for table in metadata.sorted_tables:
            log.item('Creating table {}'.format(str(table.name)))
        metadata.create_all(db.engine(metakey=metakey))
        print()

@drop.command()
def drop_cmd(connections: str = connection_arg):
    """Drop tables for connection(s)"""
    #log.header('Dropping tables for connections: [' + connections + ']')
    metakeys = get_metakeys(connections)
    for metakey in metakeys:
        log.header('Dropping tables from {} in topologically order'.format(metakey))
        metadata = db.metadata(metakey=metakey)
        for table in reversed(metadata.sorted_tables):
            log.item('Dropping table {}'.format(str(table.name)))
        metadata.drop_all(db.engine(metakey=metakey))
        print()

@recreate.command()
def recreate_cmd(connections: str = connection_arg):
    """Recreate (drop/create) tables for connection(s)"""
    #log.header('Recreating (drop/create) tables for connections: [' + connections + ']')
    drop_cmd(connections)
    create_cmd(connections)

@seed.command()
def seed_cmd(connections: str = connection_arg):
    """Seed tables for connection(s)"""
    metakeys = get_metakeys(connections)
    ran = []
    for metakey in metakeys:
        packages = db.packages(metakey=metakey)
        for package in packages:
            for seeder in package.seeders:
                if seeder not in ran:
                    log.header('Seeding tables from {} in defined order'.format(seeder))
                    module.load(seeder).object()
                    ran.append(seeder)
                    print()

@reseed.command()
def reseed_cmd(connections: str = connection_arg):
    """Reseed (drop/create/seed) tables for connection(s)"""
    recreate_cmd(connections)
    seed_cmd(connections)

@connections.command()
def connections_cmd():
    """Show all packages database connections"""
    log.header("All deep merged database connections from all defined packages").line()
    log.notice("Some connections share the same database which means their tables are in the same metedata space.  This is what the unique metakey denotes.")
    dump(db.connections)