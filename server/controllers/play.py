#!/usr/bin/env python
"""
    Login controller for ropeclient server
    Copyright (C) 2010 - 2016  Matti Eiden

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
"""

import logging
from controllers.base import BaseController
from utils.decorators.commands import Commands, dynamic_command
from utils.decorators.requirements import *
from utils.autonumber import AutoNumber
from utils.decorators.kwargs import fetch_account
from pony.orm import db_session, select, get
from models.database import db
from models.universe import Universe
from models.account import Account
from models.abstract import Utterance, Association, Offtopic

from models.things import Being



class State(AutoNumber):
    normal = ()


class PlayController(BaseController):
    def __init__(self, connection, account_id, universe_id):
        """
        MenuController is used for the main menu where the user can choose which universe to join or
        create a new universe.

        :param connection: Connection of the user
        :param account: Account of user user
        :param universe: Universe where the play happens
        :type connection: main.Connection
        :type account: models.account.Account
        :type universe: models.universe.Universe
        :return:
        """
        BaseController.__init__(self, connection)
        self.account_id = account_id
        self.universe_id = universe_id
        self.state = State.normal
        self.being = self.get_soul()

        self.account = None
        self.universe = None

    #TODO: db session?
    @db_session
    def handle(self, message={}):
        try:
            return BaseController.handle(self, message)
        except KeyError:
            pass

        key = message.get("k")
        value = message.get("v")

        if key != "msg" or len(value) == 0:
            return

        tokens = value.split(" ")
        command = tokens[0].lower()

        # Refresh universe and account
        #universe = get(universe for universe in Universe if universe == self.universe_id)
        #account = get(account for account in Account if account.id == self.account_id)

        #command_kwargs = {
        #    "universe", universe
        #    "account", account
        #}



        # Look for a matching handler
        if command in self._commands:
            return self._commands[command](self, command, tokens[1:])

        # Look for a matching startswith handler
        for startswith_command in self._startswith.keys():
            if command.startswith(startswith_command):
                return self._startswith[startswith_command](self, command, tokens[1:])

        # Look for a matching dynamic command handler
        for dcommand in self._dynamic_commands:
            try:
                return dcommand(self, command, tokens[1:])
            except NotImplementedError:
                continue

        return self.syntax_error()

    @Commands("default", "say")
    @is_being
    def do_say(self, command, tokens):
        pass

    @gamemaster
    def do_create(self, command, tokens):
        pass

    @Commands("move")
    def do_move(self, command, tokens):
        pass

    @dynamic_command
    def do_move_dynamic(self,  command, tokens):
        pass

    @Commands("offtopic", startswith=["("])
    @fetch_account
    def do_offtopic(self, command, tokens, account):
        logging.info("Offtopic requested")
        logging.info("Command:", command)
        logging.info("Tokens:", tokens)
        logging.info("Account:", account)


    @Commands("roll", startswith=["!"])
    def do_roll(self, command, tokens):

        pass

    @db_session
    def get_soul(self):
        logging.info("Got account {}".format(str(self.account_id)))
        being = get(being for being in Being if being.account is self.account_id and being.soul)
        if not being:
            logging.info("Create a new being for the player")
            place = self.universe.get_spawn()
            logging.info("Derp")
            db.commit()

            being = Being(name="Soul of {}".format(self.account_id.name),
                          account=self.account_id,
                          universe=self.universe,
                          place=place,
                          soul=True)

        else:
            logging.info("Found being")

        return being

