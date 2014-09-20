from core import Core
from database import Database, StrictRedis
import logging


class CharacterManager(Database):
    def __init__(self, core, client, world):
        """
        CharacterManager provides interface for database actions involving
        listing, creating and deleting character objects.

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

        logging.info("Creating character interface instances for world {}..".format(world.ident))
        for ident in idents:
            assert isinstance(ident, str)
            if ident not in self.interfaces:
                logging.info("Loading new character (ident: {}, world: {})".format(ident, world.ident))
                self.interfaces[ident] = Character(core, client, ident, world)

                if not self.interfaces[ident].get("location"):  #TODO: REMOVE
                    logging.warning("Character is missing a location")
                    self.interfaces[ident].set("location", self.world.locations.list()[0])

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

    '''
    def list(self):
        """

        @return: list of character idents
        """
        idents = self.client.smembers(self.path("list"))
        return idents  # TODO: Generate dict
    '''
    def new(self, name, owner_ident, location_ident, **kwargs):
        """

        Used to create a new character

        @param name: Character name
        @param password: Player password
        @param **kwargs: Optional
        @type name: str
        @type password: str
        @return:
        """
        assert isinstance(name, str)

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
        self.rpush("list", ident)

        # Create character object
        character = Character(self.core, self.client, ident, self.world)
        assert isinstance(character, Database)  # PyCharm assert hint

        # Update interfaces (we already verified the ident is unique above)
        self.interfaces[ident] = character

        # Add details
        character.set("name", name)
        character.set("owner", owner_ident)
        character.set("location", location_ident)

        # Add character to owner list
        self.rpush("owners:{}".format(owner_ident), character.ident)

        # Add character to location
        self.world.locations.add_character(location_ident, ident)


        logging.info("New character created successfully!")

    def path(self, *args):
        """
        Path to world root (rp:worlds) and optional key (arg0)

        @param args: Optional key
        @return:
        """

        if len(args) > 0 and isinstance(args[0], str):
            return "rp:worlds:{}.characters.{}".format(self.world.ident, args[0])
        else:
            return "rp:worlds:{}.characters".format(self.world.ident)

    def get_player_characters(self, player):
        """

        @return: list of character idents that belong to the player
        """
        # rp:worlds:x.characters.owners:ident -> set of character idents
        path = "owners:{}".format(player.ident)
        return self.lrange(path, 0, -1)


class Character(Database):
    def __init__(self, core, client, ident, world):
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
        #assert isinstance(world, World))

        Database.__init__(self, core=core, client=client)
        self.ident = ident
        self.world = world
        self.player = None

    def path(self, *args):
        """ Provides path for character objects

        @param args: May contain optionally a key or list of keys
        @return:
        """

        if len(args) == 0:
            return "rp:worlds:{}.characters:{}".format(self.world, self.ident)

        elif len(args) == 1 and isinstance(args[0], str):
            return "rp:worlds:{}.characters:{}.{}".format(self.world.ident, self.ident, args[0])

        else:
            keys = list(args)
            for i, k in enumerate(keys):
                keys[i] = "rp:worlds:{}.characters:{}.{}".format(self.world.ident, self.ident, k)
            return keys


    def message(self, message_ident):
        """ Store a message into character memory
        @param message: either a string or an ident referring to a stored message
        @return:
        """

        # Store message or message ident
        #self.lpush("messages", message)
        try:
            message_ident = int(message_ident)
        except ValueError:
            logging.error("message_ident should be an ident. got ({}) instead".format(message_ident))

        self.rpush("messages", message_ident)

        self.deliver_unread_messages()

    def deliver_unread_messages(self):
        """ Search for unread messages and deliver them to the player

        @return:
        """
        # TODO display a snip of history as context and color it faded
        # Require a player
        if not self.player:
            return

        lastread = self.get("messages.lastread")
        if not lastread:
            lastread = 0

        lastread = int(lastread) + 1
        lastunread = self.llen("messages")-1
        logging.info("From {} to {}".format(lastread, lastunread))

        # Fetch the idents
        unread_message_idents = self.lrange("messages",lastread, lastunread)

        logging.info("unread_messages_idents len: {}".format(len(unread_message_idents)))
        logging.info("said idents: {}".format(str(unread_message_idents)))
        # Reset lastread counter
        self.set("messages.lastread", str(self.llen("messages") - 1))

        messages = []

        for message_ident in unread_message_idents:
            message = self.world.hget("messages:{}".format(message_ident), "value")
            if not message:
                logging.warning("Was unable to fetch message (ident:{}".format(message_ident))
                continue
            else:
                messages.append(message)
        if len(messages) > 0:
            self.player.send_message(messages)
        else:
            logging.info("No unread messages")


    def attach(self, player):
        self.player = player
        self.player.character = self

        self.deliver_unread_messages()


    def detach(self):
        self.player.character = None
        self.player = None
