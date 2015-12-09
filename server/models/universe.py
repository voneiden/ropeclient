__author__ = 'wizard'
from pony.orm import PrimaryKey, Required, Optional, Set
from database import db

class Universe(db.Entity):
    from place import Place
    id = PrimaryKey(int, auto=True)
    name = Required(str, 128)
    places = Set(Place)
    password = Optional(str, 64)
    salt = Optional(str, 64)
    god_accounts = Set("Account")
    offtopics = Set("Offtopic")

