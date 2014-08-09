import logging

#import server

class Handler(object):
    def __init__(self, player):
        self.player = player
        self.core = player.core
        
    def process_msg(self, content):
        return False
        
    def process_cmd(self, content):
        return False
        
    def process_edi(self, content):
        return False
        
    def process_pit(self, content):
        return False
        
    def process_pnt(self, content):
        return False
        
    def process_pwd(self, content):
        return False
        
    def process_nan(self, content):
        logging.error("Undefined cmd in message content")


class HandlerGame(Handler):
    """
        state 0 - character selection
        state 1 - in character
        state 10 - character creation
    """
    def __init__(self, player):
        """
        This handler handles the main menu where user can choose to join and create new worlds

        @param player:
        @type player: player.Player
        @return:
        """
        Handler.__init__(self, player)
        self.state = 0

        # TODO initialize stuff
        self.player.character = None

        # TODO refill offtopic chat
        self.player.clear()
        self.player.world.send_oft_history(self.player)
        self.show_character_menu()

    def process_msg(self, message):
        """
        Processes incoming messages while joined in a world.

        @param message:
        """
        # Verify that the message has a valid payload
        if "value" not in message or len(message["value"]) == 0:
            logging.warning("process_msg no value in message")
            return

        # Character menu
        if self.state == 0:
            if message["value"].lower()[0] == "c":
                self.state = 10
                self.player.send_message("Choose a name for your new character. Please capitalize the name properly.")
                return
            try:
                ident = int(message["value"])
                logging.debug("Character requested!")
                return

            except ValueError:
                pass

        # Character spawning TODO: this should be done with a command
        if self.state == 10:
            name = message["value"]
            if len(name) > self.player.core.settings["max_character_name_length"]:
                self.player.send_message("Character name is too long (max {} letters)".format(self.player.core.settings["max_character_name_length"]))
                return
            self.player.world.characters.new(name, self.player.ident)
            self.state = 0
            self.show_character_menu()
            return

        elif message["value"][0] == "(" or not self.player.character:
            self.player.world.do_offtopic(message["value"], owner=self.player)

    def show_character_menu(self):
        self.player.clear("msg")
        buf = []
        if self.state == 0:
            # Get list of characters owned by player
            character_idents = self.player.world.characters.get_player_characters(self.player)

            assert isinstance(character_idents, list)
            if len(character_idents) == 0:
                buf.append("You have no characters. To create a new character, type 'create'.")
            else:
                buf.append("Choose from the following characters or type 'create' for a new character.")
                for i, ident in enumerate(character_idents):
                    character = self.player.world.characters.fetch(ident)
                    buf.append("{}) {}".format(i, character.get("name")))

        self.player.send_message(buf)

    def process_pit(self, content):
        self.player.typing = True
        self.player.world.send_player_typing(self.player)

    def process_pnt(self, content):
        self.player.typing = False
        self.player.world.send_player_typing(self.player)

class HandlerLogin(Handler):
    """
        state 0 msg - receiving username

    """
    def __init__(self, player):
        """

        @param player:
        @type player: server.WebPlayer
        @return:
        """
        Handler.__init__(self, player)
        self.state = 0
        self.name = None
        self.password = None
        self.ident = None

    def process_msg(self, message):
        logging.info(message)
        if len(message["value"]) == 0:
            return
            
        # State 0 - Received username
        if self.state == 0: 
            self.name = message["value"]

            # Test max length
            if len(self.name) > self.player.core.settings["max_login_name_length"]:
                self.player.send_message_fail("Login name is too long. Your name?")
                return

            # Test account has only characters
            if not self.name.isalpha():
                self.player.send_message_fail("Login name may not contain numbers or special characters. Your name?")
                return

            # Test if account exists
            ident = self.core.players.hget("names", self.name.lower())
            if ident:
                self.ident = ident
                self.player.send_message("Account found!")
                self.state = 1
                self.player.send_message("Password?")
                self.player.send_password()
                return
            else:
                self.player.send_message("Account not found! Create a new one? (y/n)")
                self.state = 10
                return

        elif self.state == 10:
            if message["value"][0].lower() == "y":
                self.state = 11
                self.player.send_message("Password?")
                self.player.send_password()
            else:
                self.state = 0
                self.player.send_message("Your name?")

        else:
            self.player.send_message("Something went wrong, restarting. Your name?")
            self.state = 0

    def process_pwd(self, pwd):
        if len(pwd["value"]) == 0:
            return

        if self.state == 1:  # Login attempt
            player = self.core.players.fetch(self.ident)

            if pwd["value"] == player.get("password"):
                self.player.send_message("Password correct!")

                # Link connection and player interface together
                player.connection = self.player

                # This sets the WebPlayers player attribute to point to the player interface (awkward..)
                self.player.player = player

                # Create handler for player interface
                player.handler = HandlerWorld(player)

            else:
                self.player.send_message("Password incorrect! Your name?")
                self.state = 0

        elif self.state == 11:  # Registering a new password
            self.password = pwd["value"]
            logging.info("Got pwd: {}".format(self.password))
            self.player.send_message("Repeat password")
            self.player.send_password()
            self.state = 12

        elif self.state == 12:  # Password retype check
            if self.password == pwd["value"]:
                self.core.players.new(self.name, self.password)
                self.player.send_message("Account created. You may now login. Your name?")
                self.state = 0
            else:
                self.player.send_message("Passwords mismatch. Try again. Your password?")
                self.player.send_password()
                self.state = 11

        else:
            self.player.send_message("Something went wrong, restarting. Your name?")
            self.state = 0


class HandlerWorld(Handler):
    def __init__(self, player):
        """
        This handler handles the main menu where user can choose to join and create new worlds

        @param player:
        @type player: player.Player
        @return:
        """
        Handler.__init__(self, player)
        self.state = 0

        self.show_menu()

    def process_msg(self, message):
        if "value" not in message or len(message["value"]) == 0:
            return

        msg = message["value"]

        if self.state == 0:
            if msg[0].lower() == "c":
                self.player.send_message("Creating new worlds is not yet supported")
                return

            try:
                ident = str(int(msg))

            except ValueError:
                self.show_menu()
                self.player.send_message_fail("Invalid command")
                return

            world = self.core.worlds.fetch(ident)
            if not world:
                self.show_menu()
                self.player.send_message_fail("World number not found")
                return

            else:
                self.player.world = world
                self.player.send_message("Joining world '{}'".format(world.get("name")))

                self.player.handler = HandlerGame(self.player)

                self.player.world.add_player(self.player)







    def show_menu(self):
        buf = [""]

        worlds = self.core.worlds
        world_idents = worlds.list()
        for ident in world_idents:
            world = worlds.fetch(ident)
            world_name = world.get("name")

            # TODO number of players online!
            buf.append("{ident}) {name}".format(ident=ident, name=world_name))

        buf.append("")
        buf.append("Choose a world to join by typing the number, or 'create' to create a new world")

        self.player.send_message(buf)


















































