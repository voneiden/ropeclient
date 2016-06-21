__author__ = 'wizard'
from pony.orm import PrimaryKey, Required, Optional, Set, db_session
from models.database import db
import utils.crypt

class Universe(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, 128, unique=True)
    places = Set("Place")
    password = Optional(str, 64)
    salt = Optional(str, 64)
    god_accounts = Set("Account")
    offtopics = Set("Offtopic")

    @classmethod
    @db_session
    def create(cls, name, owner, password=None):
        """

        :param name: Name of the universe
        :param owner: Account of the universe owner
        :param password: Password, or none
        :type name: str
        :type owner: models.account.Account
        :type password: str
        :return:
        """

        universe = cls(name=name)
        if password:
            universe.salt = utils.crypt.generate_salt()
            universe.password = utils.crypt.hash(password, universe.salt)
        universe.god_accounts.add(owner)