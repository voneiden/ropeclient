import logging
import hashlib
import base64
import os


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
            try:
                character_idents = self.player.world.characters.get_player_characters(self.player)
                enumerated_ident = int(message["value"])
                if enumerated_ident < 1:
                    self.player.send_message("Don't be silly.")
                    return
                logging.info("Character requested!")
                try:
                    ident = character_idents[enumerated_ident-1]
                except IndexError:
                    self.player.send_message("Don't be silly.")
                    return

                # Clear message window and attach character
                self.player.clear("msg")
                character = self.player.world.characters.fetch(ident)
                character.attach(self.player)
                self.state = 1

                logging.info(character)

                return

            except ValueError:
                pass

        # Offtopic messages
        if message["value"][0] == "(" or not self.player.character:
            # Strip bracket
            if message["value"][0] == "(":
                message["value"] = message["value"][1:]

            # Verify that the message is not empty and deliver it
            if len(message["value"]) > 0:
                self.player.world.do_offtopic(message["value"], owner=self.player)

        elif self.player.character:
            location_ident = self.player.character.get("location")
            location = self.player.world.locations.fetch(location_ident)

            # Format the message
            say_text = self.core.format_say(self.player.character.ident, message["value"])
            message = self.core.format_input(say_text)

            # Bad message, ignore it
            if not message:
                logging.warning("Bad message, ignoring")
                return

            # Announce it to everyone present
            location.announce_to_characters(message)

    def show_character_menu(self):
        """ Shows the character menu if player is not attached to a character. Currently doesn't show otherwise

        """
        if self.state == 0:
            # Get list of characters owned by player
            buf = []
            character_idents = self.player.world.characters.get_player_characters(self.player)
            logging.info(type(character_idents))
            assert isinstance(character_idents, list)
            if len(character_idents) == 0:
                buf.append("You have no characters. To create a new character, type 'spawn' and press TAB key.")
            else:
                buf.append("Choose from the following characters or use the command 'spawn' to create new characters.")
                for i, ident in enumerate(character_idents):
                    character = self.player.world.characters.fetch(ident)
                    buf.append("{}) {}".format(i+1, character.get("name")))
            self.player.clear("msg")
            self.player.send_message(buf)

    def process_pit(self, content):
        self.player.typing = True
        self.player.world.send_player_typing(self.player)

    def process_pnt(self, content):
        self.player.typing = False
        self.player.world.send_player_typing(self.player)

    def process_spawn(self, content):
        content = content["value"]
        assert isinstance(content, list)
        if len(content) == 0:
            return

        character_name = content[0]
        if len(content) > 1:
            character_sdesc = content[1]
        if len(content) > 2:
            character_ldesc = content[2]

        #TODO: create a new character

        if self.player.character:
            location_ident = self.player.character.get("location")
        else:
            location_ident = self.player.world.locations.list()[0]

        self.player.world.characters.new(character_name, self.player.ident, location_ident)
        self.show_character_menu()


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
        self.password_salt = None
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
                player = self.core.players.fetch(ident)
                assert player

                self.player.send_message("Account found!")
                self.state = 1
                self.player.send_message("Password?")
                self.player.send_password(player.get("password.salt"))
                return
            else:
                self.player.send_message("Account not found! Create a new one? (y/n)")
                self.state = 10
                return

        # State 10 - Create new account?
        elif self.state == 10:
            if message["value"][0].lower() == "y":
                self.state = 11
                self.player.send_message("Password?")
                self.player.send_password()
            else:
                self.state = 0
                self.player.send_message("Your name?")

        # Else - restart
        else:
            self.player.send_message("Something went wrong, restarting. Your name?")
            self.state = 0

    def process_pwd(self, pwd):
        if len(pwd["value"]) == 0:
            return

        if self.state == 1:  # Login attempt
            player = self.core.players.fetch(self.ident)
            #TODO verify client salt input
            if pwd["value"] == hashlib.sha256((player.get("password") + pwd["client_salt"]).encode("utf8")).hexdigest():
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
            self.password_salt = pwd["client_salt"]

            logging.info("Got pwd: {}".format(self.password))
            self.player.send_message("Repeat password")
            self.player.send_password(self.password_salt)
            self.state = 12

        elif self.state == 12:  # Password retype check
            retyped_salt = pwd["client_salt"]
            rehashed_password = hashlib.sha256((self.password + retyped_salt).encode("utf8")).hexdigest()
            logging.info("Original password: {}".format(self.password))
            logging.info("Retyped  password: {}".format(pwd["value"]))
            logging.info("Rehashed password: {}".format(rehashed_password))

            if rehashed_password == pwd["value"]:
                self.core.players.new(self.name, self.password, self.password_salt)
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




































