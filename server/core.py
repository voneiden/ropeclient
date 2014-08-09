#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Copyright 2010-2014Matti Eiden <snaipperi()gmail.com>
"""
import logging
import sys
import re
import cgi
import webcolors

class Core(object):
    """

    """

    def __init__(self):
        # Define settings
        self.settings = {"max_login_name_length": 30, "max_character_name_length": 30}

        from database import Database
        from world import WorldManager
        from player import PlayerManager
        from character import CharacterManager

        from redis.exceptions import ConnectionError

        logger = logging.getLogger("")
        logger.handlers = []

        # Initialize logging
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s %(module)-10s:%(lineno)-3s %(levelname)-7s %(message)s',"%y%m%d-%H:%M:%S")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        logging.info("Logger configured")

        self.version = "0.f"
        self.greeting = open('motd.txt', 'r').readlines()

        # Establish redis connection
        logging.info("Creating base database object..")
        try:
            self.db = Database(password="5ec78da7e8030656a080435a0106b4a18d965511658b81496a19bb386140e7b1")
            logging.info("Database test: %s"%str(self.db.client.ping()))

        except ConnectionError:
            logging.error("Unable to establish database connection, closing server.")
            sys.exit(1)

        # Initialize world manager
        logging.info("Setting up worlds")
        self.worlds = WorldManager(core=self, client=self.db.client)
        logging.info("Loaded {0} world{1}.".format(len(self.worlds.list()), "s" if (len(self.worlds.list()) != 1) else ""))

        # Initialize player manager
        logging.info("Setting up players")
        self.players = PlayerManager(core=self, client=self.db.client)

        logging.info("Loaded {0} player{1}.".format(len(self.players.list()), "s" if (len(self.players.list()) != 1) else ""))

        #Initialize character manager


        logging.info("Server ready")

    def color_convert(self, match):
        """
        Converts a colour value into hex
        and if it's not a valid value, default to white
        """
        color = match.group()[1:-1].lower()
        if color != "reset" or color != "default":
            try:
                webcolors.name_to_hex(color) # Check if colour is a valid name
            except ValueError:
                try:
                    webcolors.normalize_hex(color) # Check if colour is a valid hex
                except AttributeError:
                    return "$(c:default)"  # Default to white
                except ValueError: #TODO solving a bug here
                    #print ("Match:",match.group())
                    return "$(c:default)"

        return "$(c:{0})".format(color)

    def sanitize(self, text):
        """
        Use this function to sanitize any user input.
        It first converts colors and then strips <>& characters
        Note it does not currently strip "
        """

        text = re.sub("\<[\w#]+?\>", self.color_convert, text)
        text = cgi.escape(text, True)

        return text

    def find(self,source,pattern,instance):
        # source = player object
        # Pattern = pattern to be found
        # Instance = Type of instances to be searched

        # First case is testing for ID number.
        try:
            ref = int(pattern)
        except ValueError:
            ref = -1

        else:
            if isinstance(instance,world.Character):
                l = source.world.characters
            elif isinstance(instance,player.Player):
                l = source.world.Players
            try:
                return [l[ref]]
            except:
                return False

        # Second case is testing for local name match, applies only to characters
        pattern = re.compile(pattern,re.IGNORECASE)

        if isinstance(instance,world.Character):
            l = source.character.location.characters

            match = [character for character in l if re.match(pattern,character.name)]
            if len(match) > 0:
                return match

        # Third case is testing for global name match, applies to rest
        if isinstance(instance,world.Character):
            l = source.world.characters
        elif isinstance(instance,player.Player):

            l = source.world.players
        else:
            l = []
        match = [object for object in l if re.match(pattern,object.name)]
        return match