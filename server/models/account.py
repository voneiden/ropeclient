__author__ = 'wizard'
from pony.orm import PrimaryKey, Required, Optional, Set, LongStr
from models.database import db


class Account(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, 32, unique=True)
    password = Required(str, 64)
    salt = Required(str, 64)
    master_universes = Set("Universe", reverse="master_accounts")

    active_being = Optional("Being", reverse="active_account")
    beings = Set("Being", reverse="account")

    offtopics = Set("Offtopic")
    universe = Optional("Universe")

