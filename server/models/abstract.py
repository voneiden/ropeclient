__author__ = 'wizard'
from pony.orm import PrimaryKey, Required, Optional, Set, LongStr
from datetime import datetime
from models.database import db


class Utterance(db.Entity):
    id = PrimaryKey(int, auto=True)
    text = Required(LongStr)
    heard = Set("Being", reverse="heard")
    being = Optional("Being", reverse="utterances")
    timestamp = Required(datetime, sql_default='CURRENT_TIMESTAMP')


class Association(db.Entity):
    id = PrimaryKey(int, auto=True)
    known_as = Required(str, 128)
    known_by = Required("Being", reverse="associations")
    being = Required("Being", reverse="known_as")


class Offtopic(db.Entity):
    id = PrimaryKey(int, auto=True)
    text = Required(LongStr)
    universe = Required("Universe")
    account = Optional("Account")
    timestamp = Required(datetime, sql_default='CURRENT_TIMESTAMP')