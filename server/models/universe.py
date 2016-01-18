__author__ = 'wizard'
from pony.orm import PrimaryKey, Required, Optional, Set
from models.database import db

class Universe(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, 128, unique=True)
    places = Set("Place")
    password = Optional(str, 64)
    salt = Optional(str, 64)
    god_accounts = Set("Account")
    offtopics = Set("Offtopic")
    