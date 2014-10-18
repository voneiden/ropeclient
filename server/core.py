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
        self.greeting = [line.strip("\n") for line in open('motd.txt', 'r')]

        # Establish redis connection
        logging.info("Creating base database object..")
        try:
            self.db = Database(password="5ec78da7e8030656a080435a0106b4a18d965511658b81496a19bb386140e7b1", decode_responses=True)
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

    @staticmethod
    def format_say(who_ident, what, to_whom_ident=None):
        assert isinstance(who_ident, int) or who_ident.isdigit()
        assert isinstance(to_whom_ident, type(None)) or isinstance(to_whom_ident, int) or to_whom_ident.isdigit()
        assert isinstance(what, str)

        how = "says"
        emotion = ""

        # Format directed message
        if not to_whom_ident:
            to_whom = ""
        else:
            to_whom = " $(i:{})".format(to_whom_ident)

        # Apply and strip emotions
        if what[-2:] == ":)":
            emotion = "smiles and "
            what = what[:-2].strip()

        elif what[-2:] == ":(":
            emotion = "frowns and "
            what = what[:-2].strip()

        # Apply (and strip) hows
        if what[-2:] == "!!":
            how = "shouts"
            what = what[:-1]

        elif what[-1] == "!":
            how = "exclaims"

        elif what[-1] == "?":
            how = "asks"

        if len(what) > 0:
            return '''$(i:{}) {}{}{}, "<talk>{}<reset>"'''.format(who_ident, emotion, how, to_whom, what)
        else:
            return False

    @staticmethod
    def format_input(text):
        """

        @param text: A user input string that can be broken down into json compatible object
        @return: dictionary
        """

        root = {"sub": []}
        stack = [root]

        re_span_separators = ["(?:![d0-9\+\-\*/]+(?:[<>=]+[0-9]+)?)",  # Dice match
                              "(?:<[0-9A-z;:\-# ]+?>)",                                 # Style match
                              "(?:\$\(i:[0-9]+\))"]                         # Name match
        re_separator = "|".join(re_span_separators)
        # (?:![d0-9\+\-\*/]+(?:[<>=]+[0-9]+)?)|(?:<[0-9A-z;:\-# ]+?>)(?:\$\(i:[0-9]+\))
        print (re_separator)
        re_test = re.compile(re_separator)
        span_separators = re.findall(re_separator, text)
        span_blocks = re.split(re_separator, text)

        print("span_separators:", span_separators, "Total", len(span_separators))
        print("span_blocks    :", span_blocks, "Total", len(span_blocks))
        root["sub"].append(span_blocks[0])

        for i, sep in enumerate(span_separators):

            sep_block = span_blocks[i+1]

            if sep == "<reset>" or sep == "<r>":
                if len(stack) > 1:
                    stack.pop()
                if len(sep_block) > 0:
                    stack[-1]["sub"].append(sep_block)
                continue

            elif sep == "<br>":
                stack[-1]["sub"].append("{}{}".format("<br>", sep_block))
                continue

            new_span = {"sub": []}
            stack[-1]["sub"].append(new_span)
            stack.append(new_span)



            # Test simple color
            if re.match("<[#0-9A-z]+?>", sep):
                color = sep[1:][:-1]
                new_span["style"] = {"color": color}
                if len(sep_block) > 0:
                    new_span["sub"].append(sep_block)
                continue

            # Test css
            elif re.match("<[0-9A-z;:\-# ]+?>", sep):
                styles = sep[1:][:-1].split(";")
                style = {}
                for s in styles:
                    if len(s.strip()) == 0:
                        continue
                    tok = s.split(":")
                    if len(tok) == 2:
                        style[tok[0]] = tok[1]
                    else:
                        logging.error("Unable to tokenize css: {}".format(styles))

                new_span["style"] = style
                if len(sep_block) > 0:
                    new_span["sub"].append(sep_block)
                continue

            # Test dice
            elif re.match("![d0-9\+\-\*/]+(?:[<>=]+[0-9]+)?", sep):
                new_span["special"] = "dice"
                # TODO: roll the dice here
                if len(stack) > 1:
                    stack.pop()
                continue

            # Test name
            elif re.match("\$\(i:[0-9]+\)", sep):
                new_span["special"] = "name"
                new_span["sub"] = sep[4:][:-1]
                if len(stack) > 1:
                    stack.pop()
                continue

            # otherwise raise warning
            else:
                logging.warning("Was unable to determine separator: {}".format(sep))

        return root

class Span(dict):
    def __init__(self):
        self["sub"] = []