from pony.orm import sql_debug

from models.database import db

from models.account import *
from models.universe import *
from models.place import *
from models.things import *
from models.abstract import *


sql_debug(True)
#db.bind("sqlite", "database.sqlite", create_db=True)
def mapping():
    db.generate_mapping(create_tables=True)
#db.commit()