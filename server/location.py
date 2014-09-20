from core import Core
from database import Database, StrictRedis
import logging


class LocationManager(Database):
    def __init__(self, core, client, world):
        """
        LocationManager provides interface for database actions involving
        listing, creating and deleting location objects.

        @param core: Core object
        @type core: Core
        @param client: Redis client object
        @type client: StrictRedis
        @param world: world ident associated with this instance
        """
        assert isinstance(core, Core)
        assert isinstance(client, StrictRedis)

        Database.__init__(self, core=core, client=client)

        self.world = world
        self.interfaces = {}  # The dictionary of player idents mapped to player instances
        idents = self.list()

        logging.info("Creating location interface instances for world {}..".format(world.ident))
        for ident in idents:
            print(type(ident), ident)
            assert isinstance(ident, str)
            if ident not in self.interfaces:
                logging.info("Loading new location (ident: {}, world: {})".format(ident, world.ident))
                self.interfaces[ident] = Location(core, client, ident, world)

    def fetch(self, ident):
        """
        Fetches an interface to the player ident
        @param ident:
        @return:
        """
        if isinstance(ident, int):
            ident = str(ident)

        assert isinstance(ident, str)
        if ident in self.interfaces:
            return self.interfaces[ident]
        else:
            return False

    def new(self, name, description="", **kwargs):
        """

        Used to create a new location

        @param name: Location name
        @param password: Player password
        @param **kwargs: Optional
        @type name: str
        @type password: str
        @return:
        """
        assert isinstance(name, str)

        logging.info("Creating a new location..")

        # Generate a new ident for the location and verify it is unused
        i_break = 0
        while True:
            ident = str(self.incr("ident"))
            if ident not in self.interfaces:
                break

            if i_break > 10:
                logging.error("Unable to generate a unique ident. Aborting.")
                return False

        # Add the ident to location members
        self.sadd("list", ident)

        # Create location object
        location = Location(self.core, self.client, ident, self.world)
        assert isinstance(location, Database)  # PyCharm assert hint

        # Update interfaces (we already verified the ident is unique above)
        self.interfaces[ident] = location

        # Add details
        location.set("name", name)
        location.set("description", description)


        # Add location to owner list
        #self.sadd("owners:{}".format(owner_ident), character.ident)

        logging.info("New location created successfully!")

    def path(self, *args):
        """
        Path to world root (rp:worlds) and optional key (arg0)

        @param args: Optional key
        @return:
        """

        if len(args) > 0 and isinstance(args[0], str):
            return "rp:worlds:{}.locations.{}".format(self.world.ident, args[0])
        else:
            return "rp:worlds:{}.locations".format(self.world.ident)

    '''
    def get_player_characters(self, player):
        """

        @return: list of character idents that belong to the player
        """
        # rp:worlds:x.characters.owners:ident -> set of character idents
        path = "owners:{}".format(player.ident)
        return self.smembers(path)
    '''

class Location(Database):
    def __init__(self, core, client, ident, world):
        """
        Loccation object provides interface to access a location entries
        in the database.

        @param core: Core object
        @param ident: Identity of the object
        @type core: Core
        @type ident: str
        """
        assert isinstance(core, Core)
        assert isinstance(client, StrictRedis)
        assert isinstance(ident, str)
        #assert isinstance(world, World))

        Database.__init__(self, core=core, client=client)
        self.ident = ident
        self.world = world

    def path(self, *args):
        """ Provides path for location objects

        @param args: May contain optionally a key or list of keys
        @return:
        """

        if len(args) == 0:
            return "rp:worlds:{}.locations:{}".format(self.world, self.ident)

        elif len(args) == 1 and isinstance(args[0], str):
            return "rp:worlds:{}.locations:{}.{}".format(self.world.ident, self.ident, args[0])

        else:
            keys = list(args)
            for i, k in enumerate(keys):
                keys[i] = "rp:worlds:{}.locations:{}.{}".format(self.world.ident, self.ident, k)
            return keys