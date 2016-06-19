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

from utils.autonumber import AutoNumber
from controllers.base import BaseController
from pony.orm import db_session, select
from models.universe import Universe
from utils.handlers import Handlers, handler_controller

class State(AutoNumber):
    normal = ()


@handler_controller
class PlayController(BaseController):
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
        self.being = None

    def handle(self, message={}):
        try:
            return BaseController.handle(self, message)
        except KeyError:
            pass

        key = message.get("k")
        value = message.get("v")
        if key != "msg" or len(value) == 0:
            return

    @Handlers("default", "say")
    def do_say(self):
        pass

