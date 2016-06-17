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

from utils.enum import AutoNumber
from controllers.base import BaseController
from pony.orm import db_session
from models.universe import Universe

class State(AutoNumber):
    main_menu = ()


class MenuController(BaseController):
    def __init__(self, connection, account):
        """
        MenuController is used for the main menu where the user can choose which universe to join or
        create a new universe.

        :param connection: Connection of the user
        :param account: Account of user user
        :type connection: main.Connection
        :type account: models.account.Account
        :return:
        """
        BaseController.__init__(self, connection)
        self.account = account
        self.state = State.main_menu
        self.main_menu_view()

    def main_menu_view(self):
        self.send_offtopic("Following universes are available:", *[universe.name for universe in self.fetch_universes()])

    @db_session
    def fetch_universes(self):
        """
        Fetch all universes.

        :return: List of all universes
        """
        return Universe.select(lambda universe: True)[:]

