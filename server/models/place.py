__author__ = 'wizard'
from pony.orm import PrimaryKey, Required, Optional, Set, LongStr
from models.database import db




class Place(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, 128)
    description = Optional(LongStr)
    beings = Set("Being")
    universe = Required("Universe")
    exits = Set("Passage", reverse="enter_from")
    entries = Set("Passage", reverse="enter_to")
    things = Set("Thing")

class Passage(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, 32)
    enter_from = Required("Place", reverse="exits")
    enter_to = Required("Place", reverse="entries")