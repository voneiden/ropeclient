__author__ = 'wizard'
from pony.orm import PrimaryKey, Required, Optional, Set, LongStr, datetime
from database import db


class Utterance(db.Entity):
    id = PrimaryKey(int, auto=True)
    heard = Set("Being", reverse="heard")
    being = Optional("Being", reverse="utterances")


class Association(db.Entity):
    id = PrimaryKey(int, auto=True)
    known_as = Required(str, 128)
    known_by = Required("Being", reverse="associations")
    being = Required("Being", reverse="known_as")


class Offtopic(db.Entity):
    id = PrimaryKey(int, auto=True)
    universe = Required("Universe")
    account = Required("Account")
    timestamp = Required(datetime, sql_default='CURRENT_TIMESTAMP')