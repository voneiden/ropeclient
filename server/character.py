from core import Core
from database import Database, StrictRedis
import logging


class CharacterManager(Database):
    def __init__(self, core=None, client=None):
        """
        CharacterManager provides interface for database actions involving
        listing, creating and deleting player objects.

        @param core: Core object
        @type core: Core
        @type client: StrictRedis
        """
        assert isinstance(core, Core)
        assert isinstance(client, StrictRedis)

        Database.__init__(self, core=core, client=client)

        self.interfaces = {}  # The dictionary of player idents mapped to player instances
        idents = self.list()

        logging.info("Creating player interface instances..")
        for ident in idents:
            assert isinstance(ident, str)
            if ident not in self.interfaces:
                logging.info("Loading new player (ident: {})".format(ident))
                self.interfaces[ident] = Character(core, client, ident)

    def fetch(self, ident):
        """
        Fetches an interface to the player ident
        @param ident:
        @return:
        """
        assert isinstance(ident, str) or isinstance(ident, unicode)
        if ident in self.interfaces:
            return self.interfaces[ident]
        else:
            return False


    def list(self):
        """

        @return: list of character idents
        """
        idents = self.client.smembers(self.path("list"))
        return idents  # TODO: Generate dict

    def new(self, name, password, **kwargs):
        """

        Used to create a new character

        @param name: Player name
        @param password: Player password
        @param **kwargs: Optional
        @type name: str
        @type password: str
        @return:
        """
        assert isinstance(name, str)
        assert isinstance(password, str)

        logging.info("Creating a new character..")

        # Generate a new ident for the character and verify it is unused
        i_break = 0
        while True:
            ident = str(self.incr("ident"))
            if ident not in self.interfaces:
                break

            if i_break > 10:
                logging.error("Unable to generate a unique ident. Aborting.")
                return False

        # Add the ident to character members
        self.sadd("list", ident)

        # Create character object
        character = Character(core=self.core, client=self.client, ident=ident)
        assert isinstance(character, Database)  # PyCharm assert hint

        # Update interfaces (we already verified the ident is unique above)
        self.interfaces[ident] = character

        # Add details
        character.set("name", name)
        character.set("password", password)

        logging.info("New character created successfully!")

    def path(self, *args):
        """
        Path to world root (rp:worlds) and optional key (arg0)

        @param args: Optional key
        @return:
        """

        if len(args) > 0 and isinstance(args[0], str):
            return "rp:characters.{}".format(args[0])
        else:
            return "rp:characters"


class Character(Database):
    def __init__(self, core=None, client=None, ident=None):
        """
        Character object provides interface to access a player entries
        in the database.

        @param core: Core object
        @param ident: Identity of the object
        @type core: Core
        @type ident: str
        """
        assert isinstance(core, Core)
        assert isinstance(client, StrictRedis)
        assert isinstance(ident, str)

        Database.__init__(self, core=core, client=client)
        self.ident = ident

    def path(self, *args):
        """ Provides path for world objects

        @param args: May contain optionally a key or list of keys
        @return:
        """

        if len(args) == 0:
            return "rp:characters:{}".format(self.ident)

        elif len(args) == 1 and isinstance(args[0], str):
            return "rp:characters:{}.{}".format(self.ident, args[0])

        else:
            keys = list(args)
            for i, k in enumerate(keys):
                keys[i] = "rp:characters:{}.{}".format(self.ident, k)
            return keys