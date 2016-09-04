__author__ = 'wizard'
from pony.orm import PrimaryKey, Required, Optional, Set, db_session
from models.database import db
from models.place import Place
import utils.crypt

class Universe(db.Entity):
    id = PrimaryKey(int, auto=True)           # id
    name = Required(str, 128, unique=True)    # Name of the universe
    places = Set("Place")                     # All places in the universe
    password = Optional(str, 64)              # Hashed password
    salt = Optional(str, 64)                  # Salt of the password
    master_accounts = Set("Account")          # All master accounts
    offtopics = Set("Offtopic")               # All offtopic messages
    beings = Set("Being")                     # All beings in the universe
    accounts = Set("Account")                 # Logged in accounts

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
        universe.master_accounts.add(owner)

        place = Place(name="Void", universe=universe)

        return universe

    @db_session
    def get_spawn(self):
        return self.places.random(1)[0]


