__author__ = 'wizard'
from pony.orm import Database, PrimaryKey, Required
db = Database()


def db_mapping():
    import setup
    setup.mapping()