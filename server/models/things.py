__author__ = 'wizard'
from pony.orm import PrimaryKey, Required, Optional, Set, LongStr
from models.database import db



class Being(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, 128)
    description = Optional(LongStr)
    heard = Set("Utterance", reverse="heard")
    utterances = Set("Utterance", reverse="being")
    associations = Set("Association", reverse="known_by")
    known_as = Set("Association", reverse="being")
    universe = Required("Universe")
    place = Required("Place")
    things = Set("Thing")
    account = Optional("Account")
    data = Optional(LongStr)


class Thing(db.Entity):
    id = PrimaryKey(int, auto=True)
    being = Optional("Being")
    place = Required("Place")
    universe = Required("Universe")
    account = Required("Account")


