__author__ = 'wizard'
from pony.orm import PrimaryKey, Required, Optional, Set, LongStr
from models.database import db


class Account(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, 32, unique=True)
    password = Required(str, 64)
    salt = Required(str, 64)
    god_universes = Set("Universe")
    beings = Set("Being")
    offtopics = Set("Offtopic")
    thing = Optional("Thing")


