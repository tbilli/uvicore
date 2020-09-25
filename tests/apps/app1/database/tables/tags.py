import uvicore
import sqlalchemy as sa
from uvicore.database.table import Schema, SchemaOLD
from uvicore.support.dumper import dump


class _Tags(Schema):
#class Table(metaclass=SchemaOLD):

    # Actual database table name
    # Plural table names and singluar model names are encouraged
    # Do not add a package prefix, leave that to the connection config
    name = 'tags'

    # Connection for this database from your config file
    connection = 'app1'

    # SQLAlchemy Table definition as a list (exclude name and metadata)
    # This will be converted into an actual SQLAlchemy Table() instance
    # See https://docs.sqlalchemy.org/en/13/core/schema.html
    schema = [
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(length=50), unique=True),
    ]

    # Optional SQLAlchemy Table() instance kwargs
    schema_kwargs = {
        #'sqlite_autoincrement': True,
    }


# IoC Class Instance
Tags: _Tags = uvicore.ioc.make('app1.database.tables.tags.Tags', _Tags, singleton=True)
