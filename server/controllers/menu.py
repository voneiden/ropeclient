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
from controllers.play import PlayController
from pony.orm import db_session, select
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

    def handle(self, message={}):
        try:
            return BaseController.handle(self, message)
        except KeyError:
            pass

        key = message.get("k")
        value = message.get("v")
        if key != "msg" or len(value) == 0:
            return

        if self.state == State.main_menu:
            if value.lower() == "c":
                pass
            else:
                try:
                    number_choice = int(value) - 1
                    if number_choice < 0:
                        raise ValueError

                except ValueError:
                    return self.syntax_error()

                selected_universe = self.fetch_nth_universe(number_choice)
                if not selected_universe:
                    return self.main_menu_view(error_message="No such number was found..")

                print("Selected universe:", selected_universe)
                self.connection.controller = PlayController(self.account, selected_universe[0])

    def main_menu_view(self, error_message=""):
        buffer = ["Following universes are available:", ""]
        buffer += ["{N}) {name}".format(N=i+1,
                                        name=universe.name)
                   for i, universe in enumerate(self.fetch_universes())]
        buffer += ["", "To join a universe, type its number. Alternatively to create a new universe, type 'c'"]

        if error_message:
            buffer.append("<fail>{message}<reset>".format(message=error_message))

        self.send_offtopic(*buffer, clear=True)

    @db_session
    def fetch_universes(self):
        """
        Fetch all universes.

        :return: List of all universes
        """
        return Universe.select(lambda universe: True)[:]

    @db_session
    def fetch_nth_universe(self, nth):
        return select(universe for universe in Universe)[nth:nth+1]


