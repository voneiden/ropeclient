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

from controllers.base import BaseController
from utils.decorators.commands import Commands, dynamic_command
from utils.decorators.requirements import *
from utils.autonumber import AutoNumber
from pony.orm import db_session, select, get
from models.things import Thing


class State(AutoNumber):
    normal = ()


class PlayController(BaseController):
    @db_session
    def __init__(self, connection, account, universe):
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
        self.account = account
        self.universe = universe
        self.state = State.normal

        self.thing = get(account for account in self.universe.things if account == self.account)
        if not self.thing:
            self.thing = Thing(account=self.account, universe=self.universe)
            # TODO place!

        self.being = None

    #TODO: db session?
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
    @being
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
    def do_offtopic(self, command, tokens):
        pass

    @Commands("roll", startswith=["!"])
    def do_roll(self, command, tokens):
        pass