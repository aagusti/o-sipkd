import os
import subprocess
import sys
import transaction
from sqlalchemy import (
    engine_from_config,
    select,
    )
from sqlalchemy.schema import CreateSchema
from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from ..models import (
    init_model,
    DBSession,
    Base,
    )

from ..models.pemda import *
from ..models.ak import *
from ..models.ag import *
from ..models.ar import *

#from ..models.eis import *

import initial_data
from tools import mkdir


ALEMBIC_CONF = """    
[alembic]
script_location = ziggurat_foundations:migrations
sqlalchemy.url = {{db_url}}

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""    
    


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)

def create_schema(engine, schema):
    sql = select([('schema_name')]).\
          select_from('information_schema.schemata').\
          where("schema_name = '%s'" % schema)
    q = engine.execute(sql)
    if not q.fetchone():
        engine.execute(CreateSchema(schema))

def create_schemas(engine):
    for schema in ['apbd', 'eis']:
        create_schema(engine, schema)

def read_file(filename):
    f = open(filename)
    s = f.read()
    f.close()
    return s

def main(argv=sys.argv):
    def alembic_run(ini_file):
        s = read_file(ini_file)
        s = s.replace('{{db_url}}', settings['sqlalchemy.url'])
        f = open('alembic.ini', 'w')
        f.write(s)
        f.close()
        subprocess.call(command)
        os.remove('alembic.ini')

    if len(argv) != 2:
        usage(argv)
    
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    if settings['static_files']:
        mkdir(settings['static_files'])
    # Create Ziggurat tables
    bin_path = os.path.split(sys.executable)[0]
    alembic_bin = os.path.join(bin_path, 'alembic') 
    command = (alembic_bin, 'upgrade', 'head')    
    alembic_run('alembic.ini.tpl')
    alembic_run('alembic_upgrade.ini.tpl')
    # Insert data
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    init_model()
    create_schemas(engine)
    Base.metadata.create_all(engine)
    initial_data.insert()
    transaction.commit()
